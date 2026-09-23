package com.srps.db;

import com.srps.model.Paper;
import com.srps.model.User;

import java.io.File;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class DatabaseManager {
    
    private static String getDbPath() {
        String prop = System.getProperty("srps.db.path");
        if (prop != null) {
            return prop;
        }
        return "../database/papers.db";
    }

    public static Connection getConnection() throws SQLException {
        String url = "jdbc:sqlite:" + getDbPath();
        return DriverManager.getConnection(url);
    }

    private static String hashPassword(String password) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(password.getBytes());
            StringBuilder hexString = new StringBuilder();
            for (byte b : hash) {
                String hex = Integer.toHexString(0xff & b);
                if (hex.length() == 1) hexString.append('0');
                hexString.append(hex);
            }
            return hexString.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    public static User authenticateUser(String username, String password) {
        String query = "SELECT * FROM users WHERE username = ? AND password_hash = ?";
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(query)) {
            pstmt.setString(1, username);
            pstmt.setString(2, hashPassword(password));
            try (ResultSet rs = pstmt.executeQuery()) {
                if (rs.next()) {
                    return new User(
                            rs.getInt("id"),
                            rs.getString("username"),
                            rs.getString("password_hash"),
                            rs.getString("interests")
                    );
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static User registerUser(String username, String password, String interests) {
        String query = "INSERT INTO users (username, password_hash, interests) VALUES (?, ?, ?)";
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(query, Statement.RETURN_GENERATED_KEYS)) {
            String hash = hashPassword(password);
            pstmt.setString(1, username);
            pstmt.setString(2, hash);
            pstmt.setString(3, interests);
            pstmt.executeUpdate();
            try (ResultSet rs = pstmt.getGeneratedKeys()) {
                if (rs.next()) {
                    return new User(rs.getInt(1), username, hash, interests);
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return null;
    }

    public static List<Paper> getAllPapers() {
        List<Paper> papers = new ArrayList<>();
        String query = "SELECT * FROM papers";
        try (Connection conn = getConnection();
             Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(query)) {
            while (rs.next()) {
                papers.add(extractPaper(rs));
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return papers;
    }

    public static List<Paper> searchPapers(String searchQuery) {
        List<Paper> papers = new ArrayList<>();
        String query = "SELECT * FROM papers WHERE title LIKE ? OR abstract LIKE ? OR keywords LIKE ?";
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(query)) {
            String likeQuery = "%" + searchQuery + "%";
            pstmt.setString(1, likeQuery);
            pstmt.setString(2, likeQuery);
            pstmt.setString(3, likeQuery);
            try (ResultSet rs = pstmt.executeQuery()) {
                while (rs.next()) {
                    papers.add(extractPaper(rs));
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return papers;
    }

    public static List<Integer> getUserHistory(int userId) {
        List<Integer> history = new ArrayList<>();
        String query = "SELECT paper_id FROM user_history WHERE user_id = ?";
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(query)) {
            pstmt.setInt(1, userId);
            try (ResultSet rs = pstmt.executeQuery()) {
                while (rs.next()) {
                    history.add(rs.getInt("paper_id"));
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
        return history;
    }

    public static void addUserHistory(int userId, int paperId, String action) {
        String query = "INSERT INTO user_history (user_id, paper_id, action) VALUES (?, ?, ?)";
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(query)) {
            pstmt.setInt(1, userId);
            pstmt.setInt(2, paperId);
            pstmt.setString(3, action);
            pstmt.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
    
    public static void updateUserInterests(int userId, String interests) {
        String query = "UPDATE users SET interests = ? WHERE id = ?";
        try (Connection conn = getConnection();
             PreparedStatement pstmt = conn.prepareStatement(query)) {
            pstmt.setString(1, interests);
            pstmt.setInt(2, userId);
            pstmt.executeUpdate();
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }

    private static Paper extractPaper(ResultSet rs) throws SQLException {
        return new Paper(
                rs.getInt("id"),
                rs.getString("title"),
                rs.getString("abstract"),
                rs.getString("authors"),
                rs.getInt("year"),
                rs.getString("keywords"),
                rs.getString("venue"),
                rs.getString("doi")
        );
    }
}
