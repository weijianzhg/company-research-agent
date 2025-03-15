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
        with st.spinner(f"Researching {company_name}..."):
            try:
                result = agent.research_company(company_name)

                st.subheader("Research Results")

                # Company Profile
                st.markdown("### Company Profile")
                st.write(result['profile']['data'])
                st.caption(f"Source: {result['profile']['source']}")
                st.progress(result['profile']['confidence'], text=f"Confidence: {result['profile']['confidence']:.0%}")

                # Company Sector
                st.markdown("### Company Sector")
                st.write(result['sector']['data'])
                st.caption(f"Source: {result['sector']['source']}")
                st.progress(result['sector']['confidence'], text=f"Confidence: {result['sector']['confidence']:.0%}")

                # 2025 Objectives
                st.markdown("### 2025 Objectives")
                st.write(result['objectives']['data'])
                st.caption(f"Source: {result['objectives']['source']}")
                st.progress(result['objectives']['confidence'], text=f"Confidence: {result['objectives']['confidence']:.0%}")

            except Exception as e:
                st.error(f"Error during research: {str(e)}")

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

                    for idx, company in enumerate(companies):
                        with st.spinner(f"Researching {company}..."):
                            try:
                                result = agent.research_company(company)
                                results.append({
                                    'Company': company,
                                    'Profile': result['profile']['data'],
                                    'Profile Confidence': f"{result['profile']['confidence']:.0%}",
                                    'Sector': result['sector']['data'],
                                    'Sector Confidence': f"{result['sector']['confidence']:.0%}",
                                    'Objectives': result['objectives']['data'],
                                    'Objectives Confidence': f"{result['objectives']['confidence']:.0%}",
                                    'Profile Source': result['profile']['source'],
                                    'Sector Source': result['sector']['source'],
                                    'Objectives Source': result['objectives']['source']
                                })
                            except Exception as e:
                                results.append({
                                    'Company': company,
                                    'Error': str(e)
                                })
                        progress_bar.progress((idx + 1) / len(companies))

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