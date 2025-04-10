import streamlit as st
import mysql.connector
import os
from mysql.connector.cursor import MySQLCursorDict
import datetime
import pandas as pd
from decimal import Decimal

# Page configuration
st.set_page_config(
    page_title="MovieVerse",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .movie-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
        gap: 20px;
    }
    .movie-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 15px;
        transition: transform 0.3s ease;
        height: 100%;
    }
    .movie-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    .movie-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .movie-meta {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 10px;
    }
    .movie-desc {
        color: #333;
        margin-bottom: 15px;
    }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .stButton button {
        background-color: #FF4B4B;
        color: white;
        border-radius: 5px;
        border: none;
        padding: 8px 16px;
    }
    .admin-card {
        background-color: #f7f7f7;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .view-count {
        display: inline-flex;
        align-items: center;
        margin-right: 15px;
    }
    .like-count {
        display: inline-flex;
        align-items: center;
    }
    .login-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .featured-movie {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        height: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to convert decimal values
def convert_decimal(value):
    if isinstance(value, Decimal):
        return int(value)
    return value

# ----------------------------
# Database connection function
# ----------------------------
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "sql12.freesqldatabase.com"),
            user=os.getenv("DB_USER", "sql12771373"),
            password=os.getenv("DB_PASSWORD", "s5xLzgwGbt"),
            database=os.getenv("DB_NAME", "sql12771373"),
            connection_timeout=10
        )
        return conn
    except Exception as e:
        st.error("Error connecting to database: " + str(e))
        return None

# ----------------------------
# Admin authentication logic
# ----------------------------
def admin_login():
    st.markdown("<h1 style='text-align: center;'>🔐 Admin Login</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Replace st.card with container + styling
        login_container = st.container()
        with login_container:
            st.markdown("<div class='login-container'>", unsafe_allow_html=True)
            st.markdown("### Login")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.button("Login", use_container_width=True):
                conn = get_db_connection()
                if conn:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (username, password))
                    user = cursor.fetchone()
                    conn.close()

                    if user:
                        st.session_state.logged_in = True
                        st.success("Login successful!")
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
            st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------
# Admin Panel
# ----------------------------
def admin_panel():
    st.markdown("<h1 style='text-align: center;'>🎬 MovieVerse Admin Panel</h1>", unsafe_allow_html=True)

    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed")
        return
        
    cursor = conn.cursor(dictionary=True)

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🎞️ Manage Movies", "➕ Add Movie"])
    
    with tab1:
        # Dashboard with statistics
        st.subheader("Platform Statistics")
        
        # Get overall stats
        cursor.execute("SELECT COUNT(*) as total_movies, SUM(views) as total_views, SUM(likes) as total_likes FROM movies")
        stats = cursor.fetchone()
        
        # Convert Decimal values to int
        total_movies = int(stats['total_movies']) if stats['total_movies'] else 0
        total_views = int(stats['total_views']) if stats['total_views'] else 0
        total_likes = int(stats['total_likes']) if stats['total_likes'] else 0
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Movies", total_movies)
        with col2:
            st.metric("Total Views", total_views)
        with col3:
            st.metric("Total Likes", total_likes)
        
        # Most popular movies
        st.subheader("Most Popular Movies")
        cursor.execute("SELECT title, views, likes FROM movies ORDER BY views DESC LIMIT 5")
        popular_movies = cursor.fetchall()
        
        # Convert the results to a DataFrame with integer values
        popular_df = pd.DataFrame(popular_movies)
        if not popular_df.empty:
            # Convert Decimal columns to int
            if 'views' in popular_df.columns:
                popular_df['views'] = popular_df['views'].astype(int)
            if 'likes' in popular_df.columns:
                popular_df['likes'] = popular_df['likes'].astype(int)
                
            st.bar_chart(popular_df.set_index('title'))
        else:
            st.info("No movies available to display.")
    
    with tab2:
        # Manage existing movies
        st.subheader("All Movies")
        
        cursor.execute("SELECT * FROM movies ORDER BY upload_date DESC")
        movies = cursor.fetchall()
        
        if not movies:
            st.info("No movies in the database.")
        else:
            for movie in movies:
                # Convert Decimal values to int for display
                movie['views'] = int(movie['views']) if isinstance(movie['views'], Decimal) else movie['views']
                movie['likes'] = int(movie['likes']) if isinstance(movie['likes'], Decimal) else movie['likes']
                
                with st.expander(f"{movie['title']} - {movie['upload_date'].strftime('%Y-%m-%d')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Description:** {movie['description']}")
                        st.markdown(f"**Stats:** Views: {movie['views']} | Likes: {movie['likes']}")
                        st.markdown(f"**URL:** {movie['video_url']}")

                    with col2:
                        visibility = "Hidden" if movie['hidden'] else "Visible"
                        toggle_label = "Show" if movie['hidden'] else "Hide"
                        st.write(f"Status: {visibility}")
                        
                        if st.button(f"{toggle_label}", key=f"toggle_{movie['id']}"):
                            cursor.execute("UPDATE movies SET hidden = NOT hidden WHERE id = %s", (movie['id'],))
                            conn.commit()
                            st.success(f"Movie visibility updated!")
                            st.rerun()
                            
                        if st.button("Delete", key=f"delete_{movie['id']}"):
                            cursor.execute("DELETE FROM movies WHERE id = %s", (movie['id'],))
                            conn.commit()
                            st.success("Movie deleted successfully!")
                            st.rerun()
    
    with tab3:
        # Upload movie form
        st.subheader("Add New Movie")
        with st.form("upload_movie"):
            title = st.text_input("Movie Title")
            description = st.text_area("Description")
            uploaded_file = st.file_uploader("Upload Movie File", type=["mp4", "mov", "avi", "mkv", "webm", "flv", "wmv", "m4v", "3gp"])
            video_url = st.text_input("Or Enter Video URL")
            is_hidden = st.checkbox("Upload as hidden")
            submit = st.form_submit_button("Add Movie")

            if submit:
                if not (title and description and (uploaded_file or video_url)):
                    st.error("All fields are required")
                else:
                    video_path = video_url
                    if uploaded_file:
                        os.makedirs("movies", exist_ok=True)
                        file_path = f"movies/{title.replace(' ', '_').lower()}.{uploaded_file.name.split('.')[-1]}"
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.read())
                        video_path = file_path
                    
                    cursor.execute("INSERT INTO movies (title, description, video_url, hidden) VALUES (%s, %s, %s, %s)",
                                   (title, description, video_path, is_hidden))
                    conn.commit()
                    st.success(f"Movie {title} added successfully!")

    conn.close()

# ----------------------------
# User Panel
# ----------------------------
def user_panel():
    st.markdown("<h1 style='text-align: center;'>🎬 MovieVerse - Watch Movies</h1>", unsafe_allow_html=True)
    
    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed")
        return
        
    cursor = conn.cursor(dictionary=True)
    
    # Display movies
    st.subheader("Popular Movies")
    
    cursor.execute("SELECT * FROM movies WHERE hidden = 0 ORDER BY upload_date DESC LIMIT 10")
    movies = cursor.fetchall()
    
    # Movie grid layout
    if movies:
        with st.container():
            st.markdown("<div class='movie-grid'>", unsafe_allow_html=True)
            
            for movie in movies:
                st.markdown("<div class='movie-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='movie-title'>{movie['title']}</div>", unsafe_allow_html=True)
                st.image(f"movies/{movie['id']}.jpg", use_column_width=True)
                st.markdown(f"<div class='movie-desc'>{movie['description'][:150]}...</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='movie-meta'>Views: {movie['views']} | Likes: {movie['likes']}</div>", unsafe_allow_html=True)
                if st.button(f"Play {movie['title']}", key=f"play_{movie['id']}"):
                    st.video(movie['video_url'])
                st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No movies available.")
        
    conn.close()

# ----------------------------
# Main function
# ----------------------------
def main():
    # Sidebar options
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    menu = ["Home", "Admin Login", "User Panel"]
    choice = st.sidebar.selectbox("Choose your action", menu)

    if choice == "Home":
        user_panel()
    elif choice == "Admin Login":
        if st.session_state.logged_in:
            st.session_state.logged_in = False
            st.success("Logged out successfully.")
        else:
            admin_login()
    elif choice == "User Panel":
        user_panel()

if __name__ == "__main__":
    main()
