import cv2
import numpy as np
from PIL import Image  # 이미지가져오기
import os
import pandas as pd


# 이미지 로딩
def loading_img(url):
    return Image.open(url)


# 이미지를 배열로 변환
def img2arr(url):
    return np.asarray(loading_img(url))


# BGR color space -> Lab color space
def convert_BGR2CIE(url):
    return cv2.cvtColor(url, cv2.COLOR_BGR2Lab)


# 색소침착 분석시 노이즈가 되는 모공처리
def medianblur(url):
    return cv2.medianBlur(url, 19)


def remove_shadow(url):
    img = url

    # bgr을 ycbcr로 변환
    ycbcr_img = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)

    # 마스킹 이미지를 위해 이미지 카피
    binary_mask = np.copy(ycbcr_img)

    # y space 의 평균
    y_mean = np.mean(cv2.split(ycbcr_img)[0])

    # y space의 분산
    y_std = np.std(cv2.split(ycbcr_img)[0])

    # 그림자 영역과 비그림자영역 추출(마스킹)
    for i in range(ycbcr_img.shape[0]):
        for j in range(ycbcr_img.shape[1]):
            # [i,j,0]--> Y space
            if ycbcr_img[i, j, 0] < y_mean:
                # paint it white (shadow)
                binary_mask[i][j] = 255
            else:
                # paint it black (non-shadow)
                binary_mask[i][j] = 0

    # 마스킹 이미지의 노이즈 제거
    binary_mask = cv2.medianBlur(binary_mask, 19)

    # 형태학적 변환을 통해
    # 잘 분류되진 않은 픽셀을 처리
    kernel = np.ones((3, 3), np.uint8)
    erosion = cv2.erode(binary_mask, kernel, iterations=1)

    # 초기화
    # 그림자영역의 밝기
    Ld = 0  # Ld

    # 그림자영역의 밝기
    Le = 0  # Le

    # 그림자 영역의 픽셀수
    kb = 0  # kb

    # 비그림자 영역의 픽셀수
    ks = 0  # ks

    # 위 변수 구하기
    for i in range(ycbcr_img.shape[0]):
        for j in range(ycbcr_img.shape[1]):
            if erosion[i, j, 0] == 0 and erosion[i, j, 1] == 0 and erosion[i, j, 2] == 0:
                Ld = Ld + ycbcr_img[i, j, 0]
                kb += 1
            else:
                Le = Le + ycbcr_img[i, j, 0]
                ks += 1

    binary_mask = cv2.cvtColor(binary_mask, cv2.COLOR_BGR2GRAY)

    # 그림자영역의 평균 픽셀 밝기
    average_ld = Ld / kb

    # 비그림자영역의 평균 픽셀 밝기
    average_le = Le / ks

    # 밝기 비율
    ratio_ld_le = average_ld / average_le  # r

    # 밝기 차이
    diff = average_ld - average_le

    # 색 복원..
    for i in range(ycbcr_img.shape[0]):
        for j in range(ycbcr_img.shape[1]):
            if erosion[i, j, 0] == 255 and erosion[i, j, 1] == 255 and erosion[i, j, 2] == 255:
                ycbcr_img[i, j] = [ycbcr_img[i, j, 0] + diff, ycbcr_img[i, j, 1] + ratio_ld_le,
                                   ycbcr_img[i, j, 2] + ratio_ld_le]

    final_image = cv2.cvtColor(ycbcr_img, cv2.COLOR_YCR_CB2BGR)
    return final_image


def detecting_pigmentation(url):
    img = img2arr(url)
    rs = remove_shadow(img)
    img_arr = medianblur(rs)
    img_arr2 = convert_BGR2CIE(img_arr)

    # cv2_imshow(cv2.cvtColor(rs,cv2.COLOR_BGR2RGB))
    # img_arr = img2arr(url)
    # img_arr = medianblur(img_arr)
    # img_arr2 = convert_BGR2CIE(img_arr)

    L, a, b = cv2.split(img_arr2)
    Lab = [img_arr2, L, a, b]
    x = cv2.cvtColor(img_arr2, cv2.COLOR_RGB2GRAY)
    # 필터링
    # 사진의 노이즈를 제거해주는데
    # 다른(가우시안,중간값) 필터링의경우 경계선이 뭉개지는 현상이 발생
    # 색소침착 구분에있어서 색소 침착의 경계선을 찾는게 중요
    # 그런데 bilatreral fitering은 경계선을 유지해주면서 노이즈를 제거해줌
    dst = cv2.bilateralFilter(L, 3, 15, 15)

    # 균일화
    # 일반적인 이미지는 밝은 부분과 어두운 부분이 섞여 있기 때문에
    # 전체에 적용하는 것은 그렇게 유용하지 않음
    # 위처럼 하면 어두운 부분은 너무 어두워지는 현상 발생
    # 그래서 clahe 방식 도입(contrast limited adaptive histogram equalization)
    # 이미지를 작은 타일로 나누어 그 안에서 균일화를 하는 방식
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4, 4))
    L_clahe = clahe.apply(L)
    B_clahe = clahe.apply(b)

    DE = ((L / (L + a + b)) + dst) * (1 / 4) + ((L / (L + a + b)) + dst) * (1 / 2) + (
            (np.mean(L) - x) / (2 * np.mean(L))) * (dst - (L / (L + a + b)))
    DE = DE.astype(np.uint8)

    # 임계처리(이진화)
    # 기존의 threshold는 특정값을 기준으로 이진화하는데
    # adaptive는 주변 픽셀들과 상대적인 차이값을 이용하여 이진화를 한다.
    th2 = cv2.adaptiveThreshold(DE, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 101, 3)

    return th2


# 전체 화소중 침착된 화소수 찾기
def calculate_score(url):
    count = 0
    arr = detecting_pigmentation(url)
    for i in range(len(arr)):
        for j in range(len(arr[0, :])):
            if arr[i, j] == 0:
                count += 1
    # %율로 반환
    score = (count / (len(arr) * len(arr[0, :]))) * 100

    return score


# 침착영역 시각화 함수  result 디렉토리에 이미지 저장
def visualization(url):
    image = cv2.cvtColor(img2arr(url), cv2.COLOR_BGR2RGB)
    a = detecting_pigmentation(url)

    contours, hierarchy = cv2.findContours(a, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    img_con = cv2.drawContours(image, contours, -1, (0, 255, 0), 1)
    cv2.imshow('result', img_con)

    URL = "../result/{url}".format(url=url)
    cv2.imwrite(URL, img_con)

    cv2.waitKey(0)
    cv2.destroyAllWindows()

##########################################################################
# maybe deprecated

# # 필요 시 경로 수정 현재는 프로젝트 디렉토리 경로에 맞춰져 있음
# total_data = pd.read_csv("../total_all.csv")
# total_cheek_data = pd.read_csv("../total_cheek.csv")
# total_forehead_data = pd.read_csv("../total_forehead.csv")
#
# # 각 영역의 min, max값 산출
# min_total_data = total_data["total_data"].min()
# max_total_data = total_data["total_data"].max()
#
# min_cheek_data = total_cheek_data["total_cheek"].min()
# max_cheek_data = total_cheek_data["total_cheek"].max()
#
# min_forehead_data = total_forehead_data["total_forehead"].min()
# max_forehead_data = total_forehead_data["total_forehead"].max()
#

# 통합데이터내 볼 이미지 전체를 침착영역 계산해서 산술평균점수를 내어 배열에 저장하는 함수
# 계산이 오래걸림
# def calculate_process_cheek():
#     os.chdir("../integration")
#     imglist = os.listdir()
#     imglist.remove('pigmentation_score.xlsx')
#     imglist.remove('pigmentation_score2.xlsx')
#     result_all = []
#     score = 0
#     cnt = 0
#     for i in range(1, 101):
#         sum_score = 0
#         cnt = 0
#         for j in range(len(imglist)):
#             if int(sorted(imglist)[j][0:3]) == i:
#                 score = calculate_score(sorted(imglist)[j])
#                 if score > 0.1:
#                     sum_score += score
#                     cnt += 1
#         if cnt != 0:
#             result_all.append(sum_score / cnt)
#         else:
#             result_all.append(0)
#     print(len(result_all))
#     return result_all


# 볼 전체이미지에 대한 상대점수
# def calculate_process_cheek_relative():
#     scorelist = []
#     result = np.array(calculate_process_cheek())
#     for i in range(len(result)):
#         final = np.round((result[i]-min_total_data)/(max_total_data-min_total_data) * 100, 1)
#         scorelist.append(final)
#     return final


# 통합데이터내 이마 이미지전체를 침착영역 계산해서 산술평균점수를 내어 배열에 저장하는 함수
# 계산이 오래걸림   전체이미지에 대한
# def calculate_process_forehead():
#     os.chdir("forehead")
#     imglist = os.listdir()
#     # imglist.remove('pigmentation_score.xlsx')
#     result_all = []
#     score = 0
#     cnt = 0
#
#     for i in range(1, 101):
#         sum_score = 0
#         cnt = 0
#         for j in range(len(imglist)):
#             if int(sorted(imglist)[j][0:3]) == i:
#                 score = calculate_score(sorted(imglist)[j])
#                 if score > 0:
#                     sum_score += score
#                     cnt += 1
#         if cnt != 0:
#             result_all.append(sum_score / cnt)
#         else:
#             result_all.append(0)
#     print(len(result_all))
#     return result_all


# 이마 전체이미지에 대한  상대점수
# def calculate_process_forehead_relative():
#     scorelist = []
#     result = np.array(calculate_process_forehead())
#     for i in range(len(result)):
#         final = np.round((result[i]-min_total_data)/(max_total_data-min_total_data) * 100, 1)
#         scorelist.append(final)
#     return final


#########################################################################
