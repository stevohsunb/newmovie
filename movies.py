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
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "movieverse_db"),
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
                        video_path = os.path.join("movies", uploaded_file.name)
                        with open(video_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                    cursor.execute("""
                        INSERT INTO movies (title, description, video_url, upload_date, hidden, views, likes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (title, description, video_path, datetime.datetime.now(), is_hidden, 0, 0))
                    conn.commit()
                    st.success("Movie uploaded successfully")
                    st.rerun()

    conn.close()

# ----------------------------
# User Viewer Panel
# ----------------------------
def user_panel():
    st.markdown("<h1 style='text-align: center;'>🎥 Welcome to MovieVerse</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem;'>Your ultimate streaming platform for endless entertainment</p>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    
    with col1:
        search = st.text_input("🔍 Search movies", placeholder="Enter movie title...")
    
    with col2:
        sort_by = st.selectbox("Sort by", ["Newest", "Most Watched", "Most Liked"])

    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed")
        return
        
    cursor = conn.cursor(dictionary=True)

    query = "SELECT * FROM movies WHERE hidden=0"
    if search:
        query += " AND title LIKE %s"
        search_param = '%' + search + '%'
        if sort_by == "Most Watched":
            query += " ORDER BY views DESC"
            cursor.execute(query, (search_param,))
        elif sort_by == "Most Liked":
            query += " ORDER BY likes DESC"
            cursor.execute(query, (search_param,))
        else:
            query += " ORDER BY upload_date DESC"
            cursor.execute(query, (search_param,))
    else:
        if sort_by == "Most Watched":
            query += " ORDER BY views DESC"
        elif sort_by == "Most Liked":
            query += " ORDER BY likes DESC"
        else:
            query += " ORDER BY upload_date DESC"
        cursor.execute(query)

    movies = cursor.fetchall()

    # Convert Decimal values in all movies
    for movie in movies:
        movie['views'] = int(movie['views']) if isinstance(movie['views'], Decimal) else movie['views']
        movie['likes'] = int(movie['likes']) if isinstance(movie['likes'], Decimal) else movie['likes']

    # Show movies in grid layout
    st.markdown(f"### 🎞️ Showing {len(movies)} movies")
    
    if not movies:
        st.info("No movies found matching your search criteria.")
    else:
        # Use container for the movie grid
        movie_container = st.container()
        
        # Display 3 movies per row
        for i in range(0, len(movies), 3):
            with movie_container:
                cols = st.columns(3)
                for j in range(3):
                    if i+j < len(movies):
                        movie = movies[i+j]
                        with cols[j]:
                            # Replace st.card with container + styling
                            movie_box = st.container()
                            with movie_box:
                                st.markdown("<div class='movie-card'>", unsafe_allow_html=True)
                                st.markdown(f"<div class='movie-title'>{movie['title']}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='movie-meta'>📅 {movie['upload_date'].strftime('%Y-%m-%d')}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='movie-desc'>{movie['description'][:100]}...</div>", unsafe_allow_html=True)
                                
                                # Stats and like button in columns
                                col1, col2 = st.columns([3, 1])
                                with col1:
                                    st.markdown(f"👁️ **{movie['views']}** | ❤️ **{movie['likes']}**")
                                with col2:
                                    if st.button(f"Like 👍", key=f"like_btn_{movie['id']}"):
                                        cursor.execute("UPDATE movies SET likes = likes + 1 WHERE id = %s", (movie['id'],))
                                        conn.commit()
                                        st.success("You liked it!")
                                        st.rerun()
                                
                                # Play button to show video
                                if st.button(f"▶️ Play", key=f"play_{movie['id']}"):
                                    # Increment view count
                                    cursor.execute("UPDATE movies SET views = views + 1 WHERE id = %s", (movie['id'],))
                                    conn.commit()
                                    
                                    # Display video
                                    if movie['video_url'].startswith("http"):
                                        st.video(movie['video_url'])
                                    else:
                                        # Assuming local file paths
                                        st.video(movie['video_url'])
                                st.markdown("</div>", unsafe_allow_html=True)

    conn.close()

# ----------------------------
# Main App Logic
# ----------------------------
def main():
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/film-reel.png", width=100)
        st.markdown("## 🎬 MovieVerse")
        st.markdown("---")
        
        menu = st.radio("Navigate", ["🏠 Home", "👤 User Portal", "🔒 Admin Panel"])
        
        st.markdown("---")
        st.markdown("© 2023 MovieVerse Inc.")
    
    if menu == "🔒 Admin Panel":
        if "logged_in" not in st.session_state:
            admin_login()
        elif st.session_state.logged_in:
            with st.sidebar:
                if st.button("Logout", key="admin_logout"):
                    del st.session_state.logged_in
                    st.success("Logged out successfully!")
                    st.rerun()
            admin_panel()
    elif menu == "👤 User Portal":
        user_panel()
    else:  # Home
        st.markdown("<h1 style='text-align: center;'>🎬 MovieVerse</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; font-size: 1.5rem;'>Your Ultimate Streaming Platform</p>", unsafe_allow_html=True)
        
        # Featured movies or promotions
        st.markdown("## 🌟 Featured Movies")
        
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM movies WHERE hidden=0 ORDER BY RAND() LIMIT 3")
            featured_movies = cursor.fetchall()
            
            # Convert Decimal values
            for movie in featured_movies:
                movie['views'] = int(movie['views']) if isinstance(movie['views'], Decimal) else movie['views']
                movie['likes'] = int(movie['likes']) if isinstance(movie['likes'], Decimal) else movie['likes']
            
            cols = st.columns(3)
            for i, movie in enumerate(featured_movies):
                with cols[i]:
                    # Replace st.card with container + styling
                    feature_box = st.container()
                    with feature_box:
                        st.markdown("<div class='featured-movie'>", unsafe_allow_html=True)
                        st.markdown(f"### {movie['title']}")
                        st.markdown(f"👁️ {movie['views']} views | ❤️ {movie['likes']} likes")
                        st.markdown(f"{movie['description'][:100]}...")
                        if st.button("Watch Now", key=f"featured_{movie['id']}"):
                            st.session_state.menu = "👤 User Portal"
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
            
            conn.close()
        
        # App info
        st.markdown("## 📱 About MovieVerse")
        col1, col2 = st.columns(2)
        
        with col1:
            # Replace st.card with container + styling
            info_container1 = st.container()
            with info_container1:
                st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
                st.markdown("""
                ### Why Choose MovieVerse?
                - 🎥 Extensive movie collection
                - 🌐 Stream anywhere, anytime
                - 🚀 High-quality video streaming
                - 👥 User-friendly interface
                """)
                st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            # Replace st.card with container + styling
            info_container2 = st.container()
            with info_container2:
                st.markdown("<div class='admin-card'>", unsafe_allow_html=True)
                st.markdown("""
                ### Features
                - ❤️ Like your favorite movies
                - 🔍 Easy search functionality
                - 📱 Responsive design
                - 📊 Stay updated with trending movies
                """)
                st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
