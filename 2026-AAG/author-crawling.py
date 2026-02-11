import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Browser Configuration ---
options = Options()
# Disable images and stylesheets to increase scraping speed
options.add_argument("--blink-settings=imagesEnabled=false")
options.add_experimental_option("prefs", {
    "profile.managed_default_content_settings.images": 2,
    "profile.managed_default_content_settings.stylesheets": 2,
})

service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# --- Targets & Credentials ---
list_url = "https://aag-meetings.secure-platform.com/aag2026/gallery?roundId=149"
USER_ID = "" # Insert ID
USER_PW = "" # Insert PW

total_results = []
wait = WebDriverWait(driver, 8)
# Keywords to stop parsing the section to avoid irrelevant data
stop_keywords = ["abstract", "description", "session selection", "this abstract is part"]

try:
    # 1. Login Process
    driver.get(list_url)
    print("--- Attempting Login ---")
    
    id_input = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/form/div[3]/div[1]/input")))
    id_input.send_keys(USER_ID)

    pw_input = driver.find_element(By.XPATH, "/html/body/div[2]/div/div[2]/div[1]/form/div[3]/div[2]/input")
    pw_input.send_keys(USER_PW)
    pw_input.send_keys(Keys.RETURN)

    wait.until(EC.url_contains("gallery"))
    print("--- Login Successful! Starting data collection ---\n")

    current_page = 1
    max_pages = 62

    # 2. Page Iteration Loop
    while current_page <= max_pages:
        print("\n" + "=" * 70)
        print(f"{'Scraping Page ' + str(current_page) + '/' + str(max_pages):^70}")
        print("=" * 70 + "\n")

        page_results = []

        # 3. Item Iteration Loop (Standard gallery has up to 60 items per page)
        for i in range(1, 61):
            try:
                wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[1]/div[2]")))
                item_xpath = f"/html/body/div[2]/div/div[1]/div[2]/div[{i}]/div[1]/h3/a"

                try:
                    item_link = wait.until(EC.element_to_be_clickable((By.XPATH, item_xpath)))
                except:
                    print(f"[Page {current_page}] Item {i} not found - Moving to next page")
                    break

                item_url = item_link.get_attribute('href')
                print(f"[Page {current_page}, Item {i}] Entering: {item_link.text[:30]}...")
                
                # Use JS click to avoid 'element click intercepted' issues
                driver.execute_script("arguments[0].click();", item_link)

                # Wait for the detail content to load
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "section.show-if-content-block")))

                current_item_authors = []
                sections = driver.find_elements(By.CSS_SELECTOR, "section.show-if-content-block")
                author_found_start = False

                # 4. Extract Author Information
                for sec in sections:
                    text_content = sec.text.strip()

                    if "Authors:" in text_content:
                        author_found_start = True

                    if not author_found_start:
                        continue

                    clean_text = text_content.replace("Authors:", "").strip()
                    if not clean_text:
                        continue

                    if any(kw in text_content.lower() for kw in stop_keywords):
                        break

                    try:
                        # Logic to separate Name and Affiliation
                        em_tags = sec.find_elements(By.TAG_NAME, "em")
                        if em_tags:
                            affiliation = em_tags[0].text.strip()
                            full_name = clean_text.replace(affiliation, "").strip()
                        else:
                            # Fallback if <em> tag is missing
                            if "  " in clean_text:
                                parts = [p.strip() for p in clean_text.split("  ") if p.strip()]
                                full_name = parts[0]
                                affiliation = " ".join(parts[1:])
                            else:
                                full_name = clean_text
                                affiliation = "N/A"

                        # Split Name into First/Last
                        name_words = full_name.split()
                        if len(name_words) >= 2:
                            last_name = name_words[-1]
                            first_name = " ".join(name_words[:-1])
                        else:
                            last_name = full_name
                            first_name = "N/A"

                        current_item_authors.append({
                            "Page": current_page,
                            "Post_No": i,
                            "Last Name": last_name,
                            "First Name": first_name,
                            "Affiliation": affiliation,
                            "Email": "N/A",
                            "URL": item_url
                        })
                        print(f"  Added Author: {first_name} {last_name}")
                    except Exception as e:
                        print(f"  Failed to extract author details: {e}")

                # 5. Extract and Match Emails
                try:
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    contact_texts = []

                    # Attempt to find email in specific description ID
                    try:
                        elements = driver.find_elements(By.XPATH, "//div[@id='applicationJudgementDescription']/span[1]/p[2]")
                        for el in elements:
                            t = el.text.strip()
                            if t and '@' in t:
                                contact_texts.append(t)
                    except:
                        pass

                    # Fallback: Search for any paragraph containing '@'
                    if not contact_texts:
                        try:
                            elements = driver.find_elements(By.XPATH, "//p[contains(text(),'@')]")
                            for el in elements:
                                t = el.text.strip()
                                if t and '@' in t:
                                    contact_texts.append(t)
                        except:
                            pass

                    # Match found emails with extracted authors by Last Name
                    contact_texts = list(set(contact_texts))
                    for contact_text in contact_texts:
                        emails = re.findall(email_pattern, contact_text)
                        if not emails: continue

                        email = emails[0]
                        if email == USER_ID: continue # Ignore own email if present

                        words = contact_text.split()
                        words_without_email = [w for w in words if '@' not in w]

                        if len(words_without_email) >= 2:
                            potential_first = words_without_email[0]
                            potential_last = words_without_email[1]

                            for author in current_item_authors:
                                if author["Email"] != "N/A": continue
                                # Simple matching logic (Last name or First name match)
                                if author["Last Name"].lower() == potential_last.lower() or \
                                   author["Last Name"].lower() == potential_first.lower():
                                    author["Email"] = email
                                    print(f"  ✓ Email Matched: {author['First Name']} {author['Last Name']} -> {email}")
                                    break

                except Exception as e:
                    print(f"  Email extraction error: {e}")

                # 6. Save item results and navigate back
                page_results.extend(current_item_authors)
                driver.back()
                # Ensure the list view is reloaded before next item
                wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[1]/div[2]")))

            except Exception as e:
                print(f"[Page {current_page}, Item {i}] Loop Error: {e}")
                # Refresh page to recover from potential state errors
                current_page_url = f"{list_url}&page={current_page}"
                driver.get(current_page_url)
                wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[2]/div/div[1]/div[2]")))
                continue

        # 7. Incremental Backup (Save after every page)
        if page_results:
            total_results.extend(page_results)
            final_df = pd.DataFrame(total_results)
            final_df.to_excel("aag_authors_final4.xlsx", index=False)
            print(f"\n  💾 Page {current_page} Saved (Cumulative: {len(final_df)} authors)")
        else:
            print(f"\nNo data found on page {current_page}")

        # 8. Navigation to Next Page
        if current_page < max_pages:
            try:
                print(f"\nMoving to Page {current_page + 1}...")
                next_button = None
                
                # Try multiple XPATH patterns for the 'Next' button
                selectors = [
                    "//ul//a[@aria-label='next page' or @aria-label='Next']",
                    "//ul//a[normalize-space(text())='Next']",
                    "/html/body/div[2]/div/div[1]/div[4]/ul/li[last()]/a"
                ]

                for selector in selectors:
                    try:
                        next_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                        if next_button: break
                    except:
                        continue

                if next_button:
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(2) # Brief pause for stability
                    current_page += 1
                else:
                    print("✗ Next button not found - Terminating.")
                    break

            except Exception as e:
                print(f"✗ Pagination failed: {e}")
                break
        else:
            print("\nAll pages processed successfully!")
            break

    # 9. Final Summary Report
    if total_results:
        final_df = pd.DataFrame(total_results)
        print("\n" + "=" * 70)
        print(f"{'CRAWLING COMPLETE':^70}")
        print("=" * 70)
        print(f"Total Authors Collected : {len(final_df)}")
        print(f"Total Pages Processed   : {current_page}")
        print(f"Emails Found            : {len(final_df[final_df['Email'] != 'N/A'])}")
        print(f"Output File             : aag_authors_final4.xlsx")
        print("=" * 70)

except Exception as e:
    print(f"Critical Error: {e}")
    if total_results:
        pd.DataFrame(total_results).to_excel("aag_authors_final.xlsx", index=False)
        print("⚠️ Emergency backup of partial data saved.")

finally:
    driver.quit()
