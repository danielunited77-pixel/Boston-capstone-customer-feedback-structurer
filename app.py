import streamlit as st
import pandas as pd
import json
import os
from groq import Groq

# -----------------------------
# Groq API Client
# -----------------------------
import os

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# -----------------------------
# Function to classify reviews
# -----------------------------
def classify_review(review):

    prompt = f"""
You are an AI customer feedback classifier.

Choose ONLY from these labels.

Sentiment:
- Positive
- Neutral
- Negative

Issue Category:
- Battery
- Camera
- Display
- Performance
- Seller Experience
- Delivery
- Product Quality
- Network
- Price
- Accessories
- Others

Urgency:
- High
- Medium
- Low

Return ONLY valid JSON in this format:

{{
    "sentiment": "...",
    "issue_category": "...",
    "urgency": "...",
    "reason": "..."
}}

Customer Review:
{review}
"""

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        model="openai/gpt-oss-20b",
        temperature=0
    )

    response = chat_completion.choices[0].message.content

    return json.loads(response)

# -----------------------------
# Streamlit UI
# -----------------------------

st.title("AI-Powered Customer Feedback Structurer")

review = st.text_area("Enter a customer review")

if st.button("Analyze Review"):

    if review.strip():

        try:
            result = classify_review(review)

            st.subheader("Classification Result")
            st.json(result)

        except Exception as e:
            st.error(f"Error: {e}")

    else:
        st.warning("Please enter a customer review.")
# ======================================================
# Batch Review Processing
# ======================================================

st.divider()

st.header("Batch Review Processing")

uploaded_file = st.file_uploader(
    "Upload an Excel (.xlsx) or CSV file",
    type=["xlsx", "csv"]
)

if uploaded_file is not None:

    try:

        if uploaded_file.name.endswith(".csv"):
            batch_df = pd.read_csv(uploaded_file)
        else:
            batch_df = pd.read_excel(uploaded_file)

        st.success("File uploaded successfully!")
        st.write(f"Total Reviews Found: {len(batch_df)}")

        st.subheader("Preview of Uploaded Data")
        st.dataframe(batch_df.head())

        # Automatically detect the review column
        possible_review_columns = [
            "review",
            "reviews",
            "Review",
            "Review Text",
            "Customer Review",
            "Comments"
        ]

        review_column = None

        for col in possible_review_columns:
            if col in batch_df.columns:
                review_column = col
                break

        if review_column:

            st.success(f"Review column detected: {review_column}")

            if st.button("Analyze All Reviews"):

                progress_bar = st.progress(0)
                status_text = st.empty()

                total_reviews = len(batch_df)
                results = []

                for index, row in batch_df.iterrows():

                    review = str(row[review_column])

                    status_text.text(
                        f"Processing Review {index + 1} of {total_reviews}..."
                    )

                    progress_bar.progress((index + 1) / total_reviews)

                    try:

                        result = classify_review(review)

                        results.append({

                            "product_name": row.get("product_name", ""),

                            "brand_name": row.get("brand_name", ""),

                            "rating": row.get("rating", ""),

                            "review": review,

                            "sentiment": result.get("sentiment", ""),

                            "issue_category": result.get("issue_category", ""),

                            "urgency": result.get("urgency", ""),

                            "reason": result.get("reason", "")

                        })

                    except Exception as e:

                        results.append({

                            "product_name": row.get("product_name", ""),

                            "brand_name": row.get("brand_name", ""),

                            "rating": row.get("rating", ""),

                            "review": review,

                            "sentiment": "Error",

                            "issue_category": "Error",

                            "urgency": "Error",

                            "reason": str(e)

                        })
                st.success("AI Classification Completed Successfully!")

                # --------------------------------
                # Display AI Classification Results
                # --------------------------------

                results_df = pd.DataFrame(results)

                st.subheader("AI Classification Results")

                st.dataframe(results_df)

                from io import BytesIO

                excel_file = BytesIO()

                results_df.to_excel(
                    excel_file,
                    index=False,
                    engine="openpyxl"
                )

                excel_file.seek(0)
                st.download_button(
                    label="📥 Download Classified Reviews",
                    data=excel_file,
                    file_name="classified_reviews.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # ==========================================
                # KPI Dashboard
                # ==========================================

                st.divider()
                st.header("Dashboard Summary")

                col1, col2, col3, col4 = st.columns(4)

                total_reviews = len(results_df)

                positive_reviews = (results_df["sentiment"] == "Positive").sum()
                negative_reviews = (results_df["sentiment"] == "Negative").sum()
                neutral_reviews = (results_df["sentiment"] == "Neutral").sum()

                high_urgency = (results_df["urgency"] == "High").sum()

                col1.metric("Total Reviews", total_reviews)
                col2.metric("Positive", positive_reviews)
                col3.metric("Negative", negative_reviews)
                col4.metric("High Urgency", high_urgency)

                st.subheader("Most Common Issue")

                st.write(results_df["issue_category"].value_counts().head(5))

    except Exception as e:
        st.error(f"Error reading file: {e}")