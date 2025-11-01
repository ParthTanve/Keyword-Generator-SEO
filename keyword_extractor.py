import streamlit as st
import requests
import json
import pandas as pd
import urllib3
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Streamlit UI/UX Setup ---
st.set_page_config(
    page_title="SEO Keyword Generator Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("SEO Keyword Generator Tool")
st.markdown("Enter a seed keyword to discover hundreds of related suggestions using the Google Suggest API.")

# --- Core Logic Functions ---

def api_call_and_collect(query, keyword_set):
    try:
        url = "http://suggestqueries.google.com/complete/search?output=firefox&q=" + query
        response = requests.get(url, verify=False, timeout=5)
        response.raise_for_status()
        
        suggestions = json.loads(response.text)
        
        for word in suggestions[1]:
            keyword_set.add(word)
    except requests.exceptions.RequestException as e:
        pass

def run_keyword_generation(keyword, progress_bar, status_text):
    
    keyword_set = {keyword.lower()} 
    
    prefixes_list = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','y','x','y','z','how','which','why','where','who','when','are','what']    
    suffixes_list =['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','y','x','y','z','like','for','without','with','versus','vs','to','near','except','has']
    
    total_steps = len(prefixes_list) + len(suffixes_list) + 10
    current_step = 0
    
    status_text.text("Status: Initializing keyword search...")
    api_call_and_collect(keyword, keyword_set)
    
    status_text.text(f"Status: Gathering prefixes for '{keyword}'...")
    for prefix in prefixes_list:
        query = prefix + " " + keyword
        api_call_and_collect(query, keyword_set)
        
        current_step += 1
        progress_bar.progress(current_step / total_steps, 
                              text=f"Prefixes: {prefix.upper()}... | Found: {len(keyword_set)}")
        
    status_text.text(f"Status: Gathering suffixes for '{keyword}'...")
    for suffix in suffixes_list:
        query = keyword + " " + suffix
        api_call_and_collect(query, keyword_set)
        
        current_step += 1
        progress_bar.progress(current_step / total_steps, 
                              text=f"Suffixes: {suffix.upper()}... | Found: {len(keyword_set)}")
        
    status_text.text(f"Status: Checking numbers for '{keyword}'...")
    for num in range(0,10):
        query = keyword + " " + str(num)
        api_call_and_collect(query, keyword_set)

        current_step += 1
        progress_bar.progress(current_step / total_steps, 
                              text=f"Numbers: {num}... | Found: {len(keyword_set)}")
    
    status_text.text("Status: Keyword generation complete!")
    progress_bar.empty()

    return keyword_set

def clean_df(keywords, keyword):
    
    keyword_parts = keyword.lower().split(' ')
    new_list = [word for word in keywords if all(val in word.lower() for val in keyword_parts)]
    
    df = pd.DataFrame(new_list, columns=['Keywords'])
    return df

def analyze_intent(keywords):
    """Analyzes keywords to categorize user intent."""
    intent = {
        'informational': 0,
        'commercial': 0,
        'transactional': 0
    }
    
    informational_terms = ['what is', 'how to', 'guide', 'best way', 'example', 'definition']
    commercial_terms = ['best', 'top', 'review', 'vs', 'comparison', 'alternatives']
    transactional_terms = ['buy', 'price', 'deal', 'discount', 'coupon', 'for sale', 'cheap']

    for kw in keywords:
        kw_lower = kw.lower()
        if any(term in kw_lower for term in transactional_terms):
            intent['transactional'] += 1
        elif any(term in kw_lower for term in commercial_terms):
            intent['commercial'] += 1
        elif any(term in kw_lower for term in informational_terms):
            intent['informational'] += 1
            
    total = sum(intent.values())
    if total == 0:
        return intent

    # Convert to percentages
    for key in intent:
        intent[key] = round((intent[key] / total) * 100)
        
    return intent

def display_ad_strategy(df, keyword_input):
    """Generates and displays social media ad recommendations based on keyword intent."""
    
    keywords = df['Keywords'].tolist()
    intent_data = analyze_intent(keywords)
    
    st.markdown("---")
    st.header("Social Media Ad Strategy")
    st.markdown(f"Based on the **{len(keywords)}** keywords generated, here is a cross-channel strategy to target users searching for **'{keyword_input}'**:")
    
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("User Intent Analysis")
        # Display intent data in a concise way
        st.metric(label="Transactional Intent (Ready to Buy)", value=f"{intent_data['transactional']}%", help="Keywords like 'buy', 'price', 'discount'. Target on Google Ads & Retarget on Meta.")
        st.metric(label="Commercial Intent (Researching)", value=f"{intent_data['commercial']}%", help="Keywords like 'best', 'review', 'vs'. Target with YouTube Ads & Meta Lookalike Audiences.")
        st.metric(label="Informational Intent (Learning)", value=f"{intent_data['informational']}%", help="Keywords like 'how to', 'what is'. Target with content on Pinterest & Blog Posts.")

    with col_b:
        st.subheader("Platform-Specific Ad Recommendations")
        
        # Recommendation 1: High-Intent Retargeting (Meta/Facebook/Instagram)
        with st.expander("Meta Ads (Facebook / Instagram)", expanded=True):
            st.markdown(
                f"""
                **Strategy:** Retarget users who search for high-intent keywords (`{keyword_input} buy`, `{keyword_input} price`) and visit your site.
                * **Targeting:** Create a **Custom Audience** of users who visit your product page (e.g., Nike Shoes landing page) but do not purchase.
                * **Ad Content:** Offer a strong incentive (e.g., "10% OFF" or "Free Shipping") with a visually engaging Carousel or Video Ad.
                * **Goal:** Conversion / Bottom-of-Funnel.
                """
            )
            
        # Recommendation 2: Consideration & Discovery (YouTube)
        with st.expander("YouTube Ads"):
            st.markdown(
                f"""
                **Strategy:** Capture users researching before a purchase (Commercial Intent).
                * **Targeting:** Target users searching **Commercial** keywords like `{keyword_input} review` or `best {keyword_input} vs [competitor]`.
                * **Ad Content:** Use Skippable In-Stream Ads featuring product reviews, comparisons, or detailed feature explanations.
                * **Goal:** Consideration / Lead Generation.
                """
            )

# --- Streamlit Application Layout & Execution ---

col1, col2 = st.columns([3, 1])
with col1:
    keyword_input = st.text_input('**Seed Keyword**', placeholder='e.g., nike shoes', key='main_keyword')
with col2:
    st.markdown("##") 
    generate_button = st.button('Generate Keywords', type="primary")

if generate_button:
    if not keyword_input:
        st.warning("Please enter a seed keyword to begin the analysis.")
    else:
        status_text = st.empty()
        progress_bar = st.progress(0, text="Starting...")
        
        with st.spinner('Running API calls... this may take a moment.'):
            keywords_set = run_keyword_generation(keyword_input, progress_bar, status_text)
        
        if keywords_set:
            final_df = clean_df(list(keywords_set), keyword_input)
            
            st.subheader(f"Results: {len(final_df)} Unique Keywords Found")

            if not final_df.empty:
                st.dataframe(final_df, use_container_width=True, height=500, hide_index=True)
                
                csv_data = final_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download CSV File",
                    data=csv_data,
                    file_name=f'{keyword_input}-keywords.csv',
                    mime='text/csv',
                    key='download_csv'
                )

                # --- NEW FEATURE DISPLAY ---
                display_ad_strategy(final_df, keyword_input)
                
            else:
                 st.info("No related keywords found that contain the seed keyword.")