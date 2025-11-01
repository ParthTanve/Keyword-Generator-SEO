import streamlit as st
import requests
import json
import pandas as pd
import urllib3
import re
from api_urls import get_suggestion_url

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(
    page_title="SEO Keyword Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("SEO Keyword Generator Tool")
st.markdown("Enter a  keyword and select an API source (Google, YouTube, Amazon, etc.)")

def api_call_and_collect(query, keyword_set, service_url_template, api_service):
    try:
        api_service_lower = api_service.lower()
        url = None
        
        if "google" in api_service_lower or api_service_lower == 'youtube':
            url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + query
        
        elif api_service_lower in ['yahoo', 'bing', 'ebay', 'amazon']:
            base_url = "http:" + service_url_template
            
            if 'callback=?' in base_url:
                base_url = base_url.replace('callback=?', '').replace('&callback=?', '')
            
            url = base_url + query

        if not url:
            st.warning(f"Internal Error: Could not construct a valid URL for service {api_service}. Defaulting to Google API.")
            url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + query
            
        
        response = requests.get(url, verify=False, timeout=5)
        response.raise_for_status()
        suggestions = json.loads(response.text)
        
        if api_service_lower in ['google', 'youtube', 'bing', 'amazon']:
            if len(suggestions) > 1 and isinstance(suggestions[1], list):
                for word in suggestions[1]:
                    keyword_set.add(word)
        
        elif api_service_lower == 'yahoo':
            if isinstance(suggestions, dict) and 'r' in suggestions:
                for item in suggestions.get('r', []):
                    if 'k' in item:
                        keyword_set.add(item['k'])

        elif api_service_lower == 'ebay':
            if isinstance(suggestions, dict) and 'res' in suggestions:
                for item in suggestions.get('res', []):
                    if 'query' in item:
                        keyword_set.add(item['query'])

    except requests.exceptions.RequestException as e:
        pass 
    except json.JSONDecodeError as e:
        pass 


def run_keyword_generation(keyword, progress_bar, status_text, api_service):

    keyword_set = {keyword.lower()}
    service_url_template = get_suggestion_url(api_service)

    prefixes_list = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','y','x','y','z','how','which','why','where','who','when','are','what']
    suffixes_list =['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','y','x','y','z','like','for','without','with','versus','vs','to','near','except','has']

    total_steps = len(prefixes_list) + len(suffixes_list) + 10 + 1
    current_step = 0

    status_text.text(f"Status: Initializing keyword search from {api_service.upper()}...")
    api_call_and_collect(keyword, keyword_set, service_url_template, api_service)
    current_step += 1

    status_text.text(f"Status: Gathering prefixes for '{keyword}'...")
    for prefix in prefixes_list:
        query = prefix + " " + keyword
        api_call_and_collect(query, keyword_set, service_url_template, api_service)

        current_step += 1
        progress_bar.progress(current_step / total_steps,
                              text=f"Prefixes: {prefix.upper()}... | Found: {len(keyword_set)}")

    status_text.text(f"Status: Gathering suffixes for '{keyword}'...")
    for suffix in suffixes_list:
        query = keyword + " " + suffix
        api_call_and_collect(query, keyword_set, service_url_template, api_service)

        current_step += 1
        progress_bar.progress(current_step / total_steps,
                              text=f"Suffixes: {suffix.upper()}... | Found: {len(keyword_set)}")

    status_text.text(f"Status: Checking numbers for '{keyword}'...")
    for num in range(0,10):
        query = keyword + " " + str(num)
        api_call_and_collect(query, keyword_set, service_url_template, api_service)

        current_step += 1
        progress_bar.progress(current_step / total_steps,
                              text=f"Numbers: {num}... | Found: {len(keyword_set)}")

    progress_bar.progress(1.0, text="Finalizing...")
    status_text.text("Status: Keyword generation complete!")
    progress_bar.empty()

    return keyword_set

def clean_df(keywords, keyword):
    """
    Cleans keywords: keeps only those containing all parts of the seed keyword.
    """
    keyword_parts = keyword.lower().split(' ')
    new_list = [word for word in keywords if all(val in word.lower() for val in keyword_parts)]

    df = pd.DataFrame(new_list, columns=['Keywords'])
    return df

def analyze_intent(keywords):
    """Analyzes keywords to categorize user intent."""
    intent = {
        'informational': 0,
        'commercial': 0,
        'transactional': 0,
        'unclassified': 0 
    }

    informational_terms = ['what is', 'how to', 'guide', 'best way', 'example', 'definition', 'why', 'who', 'when']
    commercial_terms = ['best', 'top', 'review', 'vs', 'comparison', 'alternatives', 'good for', 'should i buy']
    transactional_terms = ['buy', 'price', 'deal', 'discount', 'coupon', 'for sale', 'cheap', 'purchase', 'order']

    for kw in keywords:
        kw_lower = kw.lower()
        if any(term in kw_lower for term in transactional_terms):
            intent['transactional'] += 1
        elif any(term in kw_lower for term in commercial_terms):
            intent['commercial'] += 1
        elif any(term in kw_lower for term in informational_terms):
            intent['informational'] += 1
        else:
            intent['unclassified'] += 1

    total = sum(intent.values())
    if total == 0:
        return intent

    classified_total = total - intent['unclassified']
    if classified_total > 0:
        for key in ['informational', 'commercial', 'transactional']:
            intent[key] = round((intent[key] / classified_total) * 100)
    
    return intent

def display_ad_strategy(df, keyword_input, api_service):
    """Generates and displays social media ad recommendations based on keyword intent and source."""

    keywords = df['Keywords'].tolist()
    intent_data = analyze_intent(keywords)

    st.markdown("---")
    st.header(f" {api_service.upper()} Keyword Strategy & Intent Analysis")
    st.markdown(f"**Source:** {api_service.upper()} | **Keywords Found:** **{len(keywords)}**")

    col_a, col_b = st.columns([1, 2])

    with col_a:
        st.subheader("User Intent Analysis")
        
        classified_total = len(keywords) - intent_data['unclassified']
        classified_total_percent = round((classified_total / len(keywords)) * 100) if len(keywords) > 0 else 0
        
        st.metric(label="Classified Keywords", value=f"{classified_total_percent}%", help="Percentage of keywords classified into one of the three main intent categories.")
        st.metric(label="Transactional Intent", value=f"{intent_data['transactional']}%", help="Keywords like 'buy', 'price', 'discount'. Target on Google Ads & Meta Retargeting.")
        st.metric(label="Commercial Intent", value=f"{intent_data['commercial']}%", help="Keywords like 'best', 'review', 'vs'. Target with YouTube Ads & Meta Lookalikes.")
        st.metric(label="Informational Intent", value=f"{intent_data['informational']}%", help="Keywords like 'how to', 'what is'. Target with content on Pinterest & Blog Posts.")
        st.metric(label="Unclassified Keywords", value=f"{intent_data['unclassified']}", help="Keywords that did not match any of the intent terms. Total Count.")

    with col_b:
        st.subheader("Platform-Specific Ad Recommendations")

        if api_service.lower() == 'youtube':
            with st.expander("YouTube & Video Content Strategy (High Priority)", expanded=True):
                st.markdown(
                    f"""
                    **Strategy:** Focus on creating **long-form video content** to capture the high **Commercial** and **Informational** intent associated with YouTube searches.
                    * **Content:** Produce high-quality `'{keyword_input} review'`, `'best {keyword_input} guide'`, and `'{keyword_input} vs [competitor]'` videos.
                    * **Ad Targeting:** Use YouTube In-Stream Ads targeting users who watch competitor videos or search for relevant commercial keywords.
                    * **Goal:** Consideration / Brand Authority.
                    """
                )
        elif api_service.lower() == 'amazon' or api_service.lower() == 'ebay':
            with st.expander("E-commerce Strategy (Amazon/eBay)", expanded=True):
                st.markdown(
                    f"""
                    **Strategy:** Target high **Transactional** intent specific to e-commerce platforms. These keywords suggest a user is close to purchase.
                    * **Platform:** Use Amazon Sponsored Product/Brand Ads or eBay Promoted Listings.
                    * **Ad Content:** Focus on **competitive pricing, shipping speed,** and **high-quality product images/videos** as the user is comparing final options.
                    * **Goal:** Conversion / Direct Sales.
                    """
                )
        else:
            with st.expander("General Digital Ad Strategy (Meta / YouTube)", expanded=True):
                st.markdown(
                    f"""
                    **Strategy:** A blend of retargeting and top-of-funnel discovery for general search.
                    * **Meta Ads (Retargeting):** Use a **Custom Audience** of users who visit your product page but don't buy. Offer a 10% discount to close the sale.
                    * **YouTube Ads (Discovery):** Use In-Stream Ads featuring product reviews or comparisons for users searching **Commercial** keywords.
                    * **Goal:** Conversion & Consideration.
                    """
                )


col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    keyword_input = st.text_input('**Seed Keyword**', placeholder='e.g., nike shoes', key='main_keyword')
with col2:
    api_source = st.selectbox(
        '**API Source**',
        ('Google', 'YouTube', 'Amazon', 'eBay', 'Bing', 'Yahoo'),
        key='api_source'
    )
with col3:
    st.markdown("##")
    generate_button = st.button('Generate Keywords', type="primary")

if generate_button:
    if not keyword_input:
        st.warning("Please enter a seed keyword to begin the analysis.")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0, text="Starting...")

        with st.spinner(f'Running API calls for {api_source.upper()}... this may take a moment.'):
            keywords_set = run_keyword_generation(keyword_input, progress_bar, status_text, api_source)

        if keywords_set:
            final_df = clean_df(list(keywords_set), keyword_input)

            st.subheader(f"Results from {api_source.upper()}: {len(final_df)} Unique Keywords Found")

            if not final_df.empty:
                st.dataframe(final_df, use_container_width=True, height=500, hide_index=True)

                csv_data = final_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV File",
                    data=csv_data,
                    file_name=f'{keyword_input}-{api_source.lower()}-keywords.csv',
                    mime='text/csv',
                    key='download_csv'
                )

                display_ad_strategy(final_df, keyword_input, api_source)

            else:
                st.info(f"No related keywords found from {api_source.upper()} that contain the seed keyword.")