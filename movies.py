import streamlit as st
import mysql.connector
import os
from datetime import datetime

# Database connection
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host='sql12.freesqldatabase.com',
            user='sql12771373',
            password='s5xLzgwGbt',
            database='sql12771373'
        )
        return conn
    except mysql.connector.Error as err:
        st.error(f"Error: {err}")
        return None

# ----------------------------
# Admin Panel
# ----------------------------
def admin_login():
    st.subheader("Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    
    if st.button("Login"):
        if username == "admin" and password == "admin":
            st.session_state.logged_in = True
            st.success("Login successful!")
        else:
            st.error("Incorrect username or password.")

def admin_panel():
    st.markdown("<h1 style='text-align: center;'>🎬 MovieVerse - Admin Panel</h1>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        admin_login()
        return
    
    conn = get_db_connection()
    if not conn:
        st.error("Database connection failed")
        return
        
    cursor = conn.cursor(dictionary=True)
    
    # Add Movie Form
    st.subheader("Add New Movie")
    
    title = st.text_input("Movie Title")
    description = st.text_area("Movie Description")
    uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mkv", "avi", "mov"])
    is_hidden = st.checkbox("Hide Movie (for Admin only)")
    
    if uploaded_file:
        file_path = os.path.join("movies", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        video_url = file_path
    else:
        video_url = st.text_input("Enter Video URL (Optional)")
    
    if st.button("Add Movie"):
        if title and description and (uploaded_file or video_url):
            cursor.execute("INSERT INTO movies (title, description, video_url, hidden) VALUES (%s, %s, %s, %s)",
                           (title, description, video_url, is_hidden))
            conn.commit()
            st.success(f"Movie {title} added successfully!")
        else:
            st.error("Please fill in all fields.")

    # Movie List and Management
    st.subheader("Manage Movies")
    cursor.execute("SELECT * FROM movies ORDER BY upload_date DESC")
    movies = cursor.fetchall()
    
    for movie in movies:
        st.write(f"**{movie['title']}**")
        st.write(movie['description'])
        st.write(f"Video URL: {movie['video_url']}")
        st.write(f"Hidden: {movie['hidden']}")
        
        # Buttons for updating or deleting
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"Edit {movie['title']}", key=f"edit_{movie['id']}"):
                # Here you can add functionality for editing movies
                st.write("Editing functionality not yet implemented.")
        with col2:
            if st.button(f"Delete {movie['title']}", key=f"delete_{movie['id']}"):
                cursor.execute("DELETE FROM movies WHERE id = %s", (movie['id'],))
                conn.commit()
                st.success(f"Movie {movie['title']} deleted successfully!")
    
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
