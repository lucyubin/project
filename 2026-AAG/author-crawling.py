import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. 브라우저 실행 및 설정
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service)

# 목적지 및 로그인 정보 설정
list_url = "https://aag-meetings.secure-platform.com/aag2026/gallery?roundId=149"
USER_ID = ""  # 아이디 입력
USER_PW = ""  # 비밀번호 입력

# 전체 데이터를 담을 리스트
total_results = []

try:
    # 2. 페이지 접속 및 로그인
    driver.get(list_url)
    wait = WebDriverWait(driver, 15)

    print("--- 로그인을 시도합니다 ---")
    id_input = wait.until(
        EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/form/div[3]/div[1]/input")))
    id_input.send_keys(USER_ID)

    pw_input = driver.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/form/div[3]/div[2]/input")
    pw_input.send_keys(USER_PW)
    pw_input.send_keys(Keys.RETURN)

    time.sleep(5)
    if "gallery" not in driver.current_url:
        driver.get(list_url)

    print("--- 데이터 수집 시작 (1~60번) ---")

    # 3. 항목 반복 루프
    for i in range(4, 6): #61
        # 3. 항목 반복 루프
        for i in range(1, 61):
            try:
                # 목록 로딩 대기
                wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[1]/div[2]")))
                item_xpath = f"/html/body/div[2]/div/div[1]/div[2]/div[{i}]/div[1]/h3/a"
                item_link = wait.until(EC.element_to_be_clickable((By.XPATH, item_xpath)))

                print(f"[{i}/60] 항목 진입 중: {item_link.text[:20]}...")
                driver.execute_script("arguments[0].click();", item_link)

                # 4. 상세 페이지 데이터 추출
                time.sleep(3)  # 상세 페이지 로딩 대기

                # 페이지 내 모든 섹션 가져오기
                sections = driver.find_elements(By.CSS_SELECTOR, "section.show-if-content-block")

                author_found_start = False

                for sec in sections:
                    text_content = sec.text.strip()

                    # 'Authors:' 문구가 보이면 그때부터 저자 수집 모드 시작
                    if "Authors:" in text_content:
                        author_found_start = True

                    if author_found_start:
                        # 텍스트가 없거나 "Authors:" 제목만 있는 섹션은 데이터가 아니므로 스킵
                        clean_text = text_content.replace("Authors:", "").strip()
                        if not clean_text:
                            continue

                        # 수집 중단 조건: 저자 정보가 끝나고 'Abstract'나 'Description' 섹션이 나오면 중단
                        if "Abstract" in text_content or "Description" in text_content or "Session Selection" in text_content:
                            break

                        # 5. 저자 정보 정제 (소속 em 태그 활용)
                        try:
                            # 소속(em 태그)이 있는지 확인
                            em_tags = sec.find_elements(By.TAG_NAME, "em")
                            if em_tags:
                                affiliation = em_tags[0].text.strip()
                                # 전체 텍스트에서 소속을 제외한 나머지를 이름으로 간주
                                full_name = clean_text.replace(affiliation, "").strip()
                            else:
                                # em 태그가 없는 경우 기존 공백 분리 방식 사용
                                if "  " in clean_text:
                                    parts = [p.strip() for p in clean_text.split("  ") if p.strip()]
                                    full_name = parts[0]
                                    affiliation = " ".join(parts[1:])
                                else:
                                    full_name = clean_text
                                    affiliation = "N/A"

                            # 성(Last Name)과 이름(First Name) 분리 (맨 뒷단어 기준)
                            name_words = full_name.split()
                            if len(name_words) >= 2:
                                last_name = name_words[-1]
                                first_name = " ".join(name_words[:-1])
                            else:
                                last_name = full_name
                                first_name = "N/A"

                            # 결과 저장
                            total_results.append({
                                "Post_No": i,
                                "Last Name": last_name,
                                "First Name": first_name,
                                "Affiliation": affiliation
                            })
                        except Exception as e:
                            print(f"개별 저자 추출 실패: {e}")

                # 뒤로 가기
                driver.back()
                time.sleep(2)

            except Exception as e:
                print(f"{i}번 항목 처리 중 오류 발생: {e}")
                driver.get(list_url)
                time.sleep(3)
                continue

    # 6. 결과 저장
    if total_results:
        final_df = pd.DataFrame(total_results)
        # 엑셀 파일로 저장
        #final_df.to_excel("aag_authors_final.xlsx", index=False)
        print("\n" + "=" * 30)
        print(f"수집 완료! 총 {len(final_df)}명의 저자 정보 저장됨.")
        print("파일명: aag_authors_final.xlsx")
        print("=" * 30)
        print(final_df)
    else:
        print("수집된 데이터가 없습니다.")

except Exception as e:
    print(f"치명적 오류: {e}")

finally:
    driver.quit()
