import streamlit as st
import pandas as pd
from research_agent import CompanyResearchAgent

st.set_page_config(
    page_title="Company Research Agent",
    page_icon="🔍"
)

st.title("Company Research Agent 🔍")

# Initialize the research agent
@st.cache_resource
def get_research_agent():
    return CompanyResearchAgent()

agent = get_research_agent()

# Input method selection
input_method = st.radio(
    "Choose input method:",
    ["Single Company", "Multiple Companies"]
)

if input_method == "Single Company":
    company_name = st.text_input("Enter company name:")

    if company_name and st.button("Research"):
        progress_container = st.empty()
        result_container = st.empty()

        try:
            # Initialize progress
            progress_container.markdown("### Research Progress")

            # Profile Search
            progress_container.markdown("🔍 Searching for company profile...")
            profile_data = agent.search_company_profile(company_name)

            if profile_data:
                with result_container.container():
                    st.markdown("### Company Profile")
                    st.write(profile_data['data'])
                    if profile_data['source'] != 'N/A':
                        st.caption(f"Source: {profile_data['source']}")
                    st.progress(profile_data['confidence'], text=f"Confidence: {profile_data['confidence']:.0%}")

            # Sector Search
            progress_container.markdown("🔍 Analyzing industry sector...")
            sector_data = agent.search_company_sector(company_name)

            if sector_data:
                with result_container.container():
                    st.markdown("### Company Sector")
                    st.write(sector_data['data'])
                    if sector_data['source'] != 'N/A':
                        st.caption(f"Source: {sector_data['source']}")
                    st.progress(sector_data['confidence'], text=f"Confidence: {sector_data['confidence']:.0%}")

            # Objectives Search
            progress_container.markdown("🔍 Finding future objectives...")
            objectives_data = agent.search_company_objectives(company_name)

            if objectives_data:
                with result_container.container():
                    st.markdown("### 2025 Objectives")
                    st.write(objectives_data['data'])
                    if objectives_data['source'] != 'N/A':
                        st.caption(f"Source: {objectives_data['source']}")
                    st.progress(objectives_data['confidence'], text=f"Confidence: {objectives_data['confidence']:.0%}")

            progress_container.markdown("✅ Research complete!")

        except Exception as e:
            st.error(f"Error during research: {str(e)}")
            st.info("Note: Partial results may be shown above if some data was found before the error occurred.")

else:
    uploaded_file = st.file_uploader("Upload CSV file with company names", type=['csv'])

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            if 'company_name' not in df.columns:
                st.error("CSV must contain a 'company_name' column")
            else:
                companies = df['company_name'].tolist()
                if st.button(f"Research {len(companies)} companies"):
                    results = []
                    progress_bar = st.progress(0)
                    status_container = st.empty()

                    for idx, company in enumerate(companies):
                        status_container.markdown(f"Researching {company}...")
                        try:
                            profile_data = agent.search_company_profile(company)
                            sector_data = agent.search_company_sector(company)
                            objectives_data = agent.search_company_objectives(company)

                            results.append({
                                'Company': company,
                                'Profile': profile_data.get('data', 'Not found'),
                                'Profile Confidence': f"{profile_data.get('confidence', 0):.0%}",
                                'Sector': sector_data.get('data', 'Not found'),
                                'Sector Confidence': f"{sector_data.get('confidence', 0):.0%}",
                                'Objectives': objectives_data.get('data', 'Not found'),
                                'Objectives Confidence': f"{objectives_data.get('confidence', 0):.0%}",
                                'Profile Source': profile_data.get('source', ''),
                                'Sector Source': sector_data.get('source', ''),
                                'Objectives Source': objectives_data.get('source', '')
                            })
                        except Exception as e:
                            results.append({
                                'Company': company,
                                'Error': str(e)
                            })
                        progress_bar.progress((idx + 1) / len(companies))

                    status_container.empty()
                    results_df = pd.DataFrame(results)
                    st.dataframe(results_df)

                    # Download button for results
                    csv = results_df.to_csv(index=False)
                    st.download_button(
                        label="Download results as CSV",
                        data=csv,
                        file_name="research_results.csv",
                        mime="text/csv"
                    )
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

st.markdown("---")
st.markdown("### Instructions")
st.markdown("""
- For single company research, enter the company name and click Research
- For multiple companies, upload a CSV file with a 'company_name' column
- Results include company profile, sector, and 2025 objectives with confidence scores and sources
- Higher confidence scores indicate more reliable information
""")