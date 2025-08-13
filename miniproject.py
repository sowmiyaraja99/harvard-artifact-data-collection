
import streamlit as st
import pandas as pd
import requests
import mysql.connector as mc
connection = mc.connect(host='127.0.0.1',user='root',password='Yadhuyazhan2207',database='project')
c = connection.cursor()
st.title("WELCOME TO HARVARD ARTIFACTS")
option = st.selectbox("QUERIES",
    ("""SELECT *from artifact_metadata where century='11th century' and 
          culture='Byzantine culture'""", 
    """select distinct culture from artifact_metadata""",
    """select *from artifact_metadata where period='Archaic Period'""",
    """select title,accessionyear from artifact_metadata order by accessionyear desc""",
    """select department,count(*) from artifact_metadata group by department""",
    """select objectid,imagecount from artifact_media where imagecount>3""",
    """select avg(`rank`) from artifact_media""",
    """select objectid from artifact_media where mediacount>imagecount""",
    """select *from artifact_media where datebegin >= 1500 and dateend<=1600""",
    """select *from artifact_media where mediacount=0""",
    """ select distinct hue from artifact_colors""",
    """SELECT color, COUNT(*) as frequency  FROM artifact_colors GROUP BY color
ORDER BY frequency DESC LIMIT 5""",
"""SELECT hue, avg(percent) from artifact_colors GROUP BY hue ORDER BY hue""",
"""select color,spectrum,hue,percent,css3 from artifact_colors where objectid=%s""",
"""select count(*) from artifact_colors""",
"""select m.title,c.hue from artifact_metadata m join artifact_colors c on
m.id=c.objectid where culture='Byzantine'""",
"""select m.title,c.hue from artifact_metadata as m join artifact_colors as c on
m.id=c.objectid""" ,
"""select m.title,m.culture,media.rank from artifact_metadata as m join 
artifact_media as media on m.id=media.objectid where m.period is not null""",
"""select distinct m.title from artifact_metadata as m join artifact_media as media on
m.id=media.objectid join artifact_colors as c on m.id=c.objectid where media.`rank` <=10 
and c.hue='grey'""",
"""select m.classification,count(*) as artifact_count,avg(media.mediacount) as avg_media_count
from artifact_metadata as m join artifact_media as media ON m.id = media.objectid GROUP BY m.classification"""
)
)

st.write("You selected:", option)

try:
    # For queries with %s placeholder (needs manual input)
    if "%s" in option:
        object_id = st.text_input("Enter object ID:")
        if object_id:
            c.execute(option, (object_id,))
            rows = c.fetchall()
            df = pd.DataFrame(rows, columns=[desc[0] for desc in c.description])
            st.dataframe(df)
    else:
        c.execute(option)
        rows = c.fetchall()
        df = pd.DataFrame(rows, columns=[desc[0] for desc in c.description])
        st.dataframe(df)
except Exception as e:
    st.error(f"Error: {e}")

st.set_page_config(page_title="Harvard Artifact Data Collector", layout="wide")
st.title("Harvard Artifact Data Collector")


classifications = ["Coins", "Paintings", "Scriptures", "Jewellery", "Drawings"]
selected_classification = st.selectbox("Select Classification", classifications)
API_KEY = "38cb2140-dc22-41ab-95ec-74fc5517c88b"
BASE_URL = "https://api.harvardartmuseums.org/object"
if "fetched_data" not in st.session_state:
    st.session_state["fetched_data"] = pd.DataFrame()

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Collect Data"):
        st.write("Fetching data from API...")
        records = []
        page = 1
        while len(records) < 2500:
            params = {
                "apikey": API_KEY,
                "classification": selected_classification,
                "size": 100,
                "page": page
            }
            r = requests.get(BASE_URL, params=params)
            data = r.json()
            records.extend(data.get("records", []))
            page += 1
        st.session_state["fetched_data"] = pd.DataFrame(records)
        st.success(f"Collected {len(st.session_state['fetched_data'])} records.")

with col2:
    if st.button("Show Data"):
        if not st.session_state["fetched_data"].empty:
            st.dataframe(st.session_state["fetched_data"].head(50))
        else:
            st.warning("No data collected yet.")

with col3:
    if st.button("Insert into SQL"):
        if not st.session_state["fetched_data"].empty:
            st.write("Inserting data into SQL...")
            for _, row in st.session_state["fetched_data"].iterrows():
                c.execute(
                    "INSERT INTO artifact_metadata (objectid, title, classification) VALUES (%s, %s, %s)",
                    (row.get("objectid"), row.get("title"), row.get("classification"))
                )
            connection.commit()
            st.success("Data inserted into SQL.")
        else:
            st.warning("No data to insert.")

st.subheader("Query & Visualization")

query_options = {
    "All artifacts from selected classification": f"SELECT * FROM artifact_metadata WHERE classification='{selected_classification}' LIMIT 50",
    "Artifacts with non-null period": "SELECT objectid, title, period FROM artifact_metadata WHERE period IS NOT NULL LIMIT 50",
    "Top 10 colors by usage": "SELECT color, COUNT(*) AS count FROM artifact_colors GROUP BY color ORDER BY count DESC LIMIT 10"
}

selected_query = st.selectbox("Select Query", list(query_options.keys()))

if st.button("Run Query"):
    c.execute(query_options[selected_query])
    result = c.fetchall()
    columns = [desc[0] for desc in c.description]
    df_result = pd.DataFrame(result, columns=columns)
    st.dataframe(df_result)

