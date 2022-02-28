# 개요    
코드설명은 각 파일에 주석을 달아두었습니다.	
파이참 환경에서 제작되어 다른 플랫폼이나 다른 환경 사용 시 파일의 경로 변경이 요구됩니다.
## 파이썬 파일
calculate_cheek_excel.py    
calculate_forehead_excel.py     
--> 이 두 파일은 각 이미지에 대한 색소침착 검출 값을 엑셀파일에 저장하는 코드입니다.  
첨부파일로 검출 데이터를 정리했기 때문에, 큰 사용성은 없는데, 중간과정에서 생성한 코드이기때문에 남겨두었습니다.

            
module.py   
--> 색소침착 검출에 있어 필요한 전처리, 검출 , 계산 , 시각화 등의 함수가 있는 파일입니다.

module_test.py  
--> 위 module.py의 test 파일입니다. 

pigmentation_module.py  
--> 신규 데이터를 입력하여, 최종 사용자의 분류를 하는 파일 입니다.        
미리 제공받은 인아웃 모듈설계와 점수화 방안 파일들을 기반으로하여 제작하였습니다.   
최종적으로 값 출력과 색소침착 영역 마스킹 이미지를 저장합니다.

## csv파일    
total_(all,cheek,forehead).csv  
--> 샘플 데이터의 각 대상자의 색소 침착 값 입니다. 산출 값 0을 제외한 값들의 평균값입니다.

each_(all,cheek,forehead).csv  
--> 개별 이미지에 대한 산출값입니다. 혹시 몰라 넣어두었습니다.   
