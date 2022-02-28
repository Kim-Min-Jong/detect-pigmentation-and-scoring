import os
import numpy as np
import pandas as pd
from module import calculate_score, visualization

# 경로 지정 요망 / 현재는 이미지를 가져오기 위해 통합이미지 디렉토리인 total_image에 맞춰져 있음
os.chdir("total_image")

# urls 에  순서대로 좌측 볼, 우측 볼, 이마 이미지 입력 (특정 폴더내, 사용자에 맞게 경로 조정 필요)
urls = ["041_2_lpp.jpg", "041_2_rpp.jpg", "041_2_fpp.jpg"]
total_score = 0
result = []

# 개별 산출값 저장
for i in range(len(urls)):
    result.append(calculate_score(urls[i]))

# 필요 시 경로 수정 현재는 data 디렉토리 경로에 맞춰져 있음
total_data = pd.read_csv("../data/total_all.csv")
total_cheek_data = pd.read_csv("../data/total_cheek.csv")
total_forehead_data = pd.read_csv("../data/total_forehead.csv")

# 각 영역의 min, max값 산출
min_total_data = total_data["total_data"].min()  # 0.0
max_total_data = total_data["total_data"].max()  # 5.028279622

min_cheek_data = total_cheek_data["total_cheek"].min()  # 0.0
max_cheek_data = total_cheek_data["total_cheek"].max()  # 5.028279622

min_forehead_data = total_forehead_data["total_forehead"].min()  # 0.0
max_forehead_data = total_forehead_data["total_forehead"].max()  # 5.950927734


# 좌측 볼, 우측볼 ,이마 전체 평균 색소침착값
score_all = np.mean(result)

# 좌측 볼, 우측볼 평균 색소침착값
score_Uzone = np.mean(result[:2])

# 이마 색소침착값
score_Tzone = result[2]

# 평균점수 배열
score_integration = [score_all, score_Uzone, score_Tzone]

# 상대 점수화 - 미리 전체 샘플을 계산하고, 그것과 각 대상자의 점수를 비교하여 상대 점수를 구함
# 전체 샘플들 대비 대상자의 색침 상대점수
score_all_relative = np.round((score_all-min_total_data)/(max_total_data-min_total_data) * 100, 1)

# u존에 대한 전체 샘플들 대비 대상자의 색침 상대점수
score_Uzone_relative = np.round((score_Uzone-min_cheek_data)/(max_cheek_data-min_cheek_data) * 100, 1)

# t존에 대한 전체 샘플들 대비 대상자의 색침 상대점수
score_Tzone_relative = np.round((score_Tzone-min_forehead_data)/(max_forehead_data-min_forehead_data) * 100, 1)

# 새로 들어온 값이 기존 샘플의 최댓값을 넘어버리면 상대점수가 100이 넘어버리기 때문에, 그럴 시 100점 고정
if score_all_relative > 100:
    score_all_relative = 100
if score_Uzone_relative > 100:
    score_all_relative = 100
if score_Tzone_relative > 100:
    score_all_relative = 100

# 상대점수 통합 배열
score_relative = [score_all_relative, score_Uzone_relative, score_Tzone_relative]

caption = ["상(나쁨)", "중(보통)", "하(좋음)"]

# 출력
print("전체 색소침착 평군값: ", score_all)
print("U존 색소침착 평균값: ", score_Uzone)
print("T존 색소침착 값: ", score_Tzone)

print("전체 대비 색소침착 상대점수(전체 최종 점수): ", score_all_relative)
print("U존 전체 대비 색소침착 상대점수(U존 최종 점수): ", score_Uzone_relative)
print("T존 전체 대비 색소침착 상대점수(T존 최종 점수): ", score_Tzone_relative)


print(f'최종 평가점수: \"{score_all_relative}\"')

# 점수 구간은 첨부 엑셀파일에 정리
if score_all < 1:
    print(f'현재 인원의 색소침착 상태는 \"{caption[2]}\" 입니다.')
else:
    if score_all <= 3:
        print(f'현재 인원의 색소침착 상태는 \"{caption[1]}\" 입니다.')
    else:
        print(f'현재 인원의 색소침착 상태는 \"{caption[0]}\" 입니다.')

# 마스킹 이미지 저장 (result 디렉토리에 저장됨)
for i in range(len(urls)):
    visualization(urls[i])
