from flask import Blueprint, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from model.zscaler import ZscalerPress
from __init__ import db

zscaler_api = Blueprint('zscaler_api', __name__, url_prefix='/api/zscaler')

# Keywords for Customer Wins
KEYWORDS = [
    "deploy", "deployment", "deployed", "implemented", "integration",
    "install", "installed", "adopted", "rollout", "onboarded", "enabled", 
    "launched", "activated", "provisioned", "initiated",
    "customer", "client", "enterprise", "organization", "company", 
    "business", "firm", "institution", "agency", "department", "government",
    "healthcare", "finance", "bank", "insurance", "education", "school", 
    "university", "telecom", "manufacturing", "retail", "technology",
    "partnership", "collaboration", "alliance", "agreement", "contract", 
    "signed", "joint", "cooperation", "engagement", "strategic", "deal", 
    "acquisition", "merger", "integration partner",
    "LATAM", "Brazil", "Mexico", "Argentina", "Chile", "Colombia",
    "Japan", "Asia", "North America", "US", "United States", "Canada",
    "Europe", "EMEA", "APAC", "Middle East", "Africa",
    "zero trust", "cloud security", "security platform", "SASE", "AI-driven", 
    "threat detection", "cybersecurity", "endpoint security", "network security",
    "firewall", "VPN", "identity", "analytics", "automation",
    "expands", "extends", "grows", "enhances", "strengthens", "boosts", 
    "accelerates", "recognized", "leader", "award", "achieves", "success"
]


@zscaler_api.route('/', methods=['GET'])
def home():
    return {"message": "Zscaler API Root"}


@zscaler_api.route('/scrape', methods=['GET'])
def scrape_zscaler():
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(options=options)
    driver.get("https://ir.zscaler.com/news-events/press-releases")

    results = []

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.nir-widget--news--headline"))
        )
    except TimeoutException:
        driver.quit()
        return jsonify({"message": "Failed to load press releases page"}), 500

    articles = driver.find_elements(By.CSS_SELECTOR, "div.nir-widget--news--headline")

    for article in articles:
        try:
            title_elem = article.find_element(By.TAG_NAME, "a")
            title = title_elem.text
            link = title_elem.get_attribute("href")

            try:
                date_elem = article.find_element(By.XPATH, "../div[contains(@class,'date-display')]")
                date = date_elem.text
            except:
                date = None

            driver.execute_script("window.open(arguments[0]);", link)
            driver.switch_to.window(driver.window_handles[1])

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".field--name-body, .article-body"))
                )
                text = driver.find_element(By.CSS_SELECTOR, ".field--name-body, .article-body").text.lower()
            except TimeoutException:
                text = ""

            driver.close() 
            driver.switch_to.window(driver.window_handles[0])  

            matched_title = [kw for kw in KEYWORDS if kw.lower() in title.lower()]
            matched_body = [kw for kw in KEYWORDS if kw.lower() in text]
            matched = list(set(matched_title + matched_body))

            if matched:
                summary = " ".join(text.split()[:50]) + "..."
                entry = ZscalerPress(
                    title=title,
                    date=date,
                    url=link,
                    summary=summary,
                    category_detected="Customer Wins",
                    keywords_matched=", ".join(matched),
                    region_detected=None
                )
                db.session.add(entry)
                results.append({
                    "title": title,
                    "date": date,
                    "url": link,
                    "keywords": matched
                })

        except Exception as e:
            print("Error scraping article:", e)
            continue

    db.session.commit()
    driver.quit()
    return jsonify({"message": f"Scraped {len(results)} relevant releases.", "data": results})

@zscaler_api.route('/all', methods=['GET'])
def get_all_press():
    records = ZscalerPress.query.all()
    return jsonify([
        {
            "id": r.id,
            "title": r.title,
            "date": r.date,
            "url": r.url,
            "summary": r.summary,
            "category_detected": r.category_detected,
            "keywords_matched": r.keywords_matched
        } for r in records
    ])
