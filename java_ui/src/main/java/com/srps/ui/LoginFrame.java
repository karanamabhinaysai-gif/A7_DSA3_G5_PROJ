package com.srps.ui;

import com.srps.db.DatabaseManager;
import com.srps.model.User;

import javax.swing.*;
import java.awt.*;

public class LoginFrame extends JFrame {
    private JTextField usernameField;
    private JPasswordField passwordField;
    private JLabel statusLabel;

    public LoginFrame() {
        setTitle("Smart Research Paper Recommendation System");
        setSize(450, 400);
        setMinimumSize(new Dimension(450, 400));
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(Color.WHITE);

        initUI();
    }

    private void initUI() {
        setLayout(new GridBagLayout());
        GridBagConstraints gbc = new GridBagConstraints();
        gbc.insets = new Insets(10, 10, 10, 10);
        gbc.fill = GridBagConstraints.HORIZONTAL;

        JLabel titleLabel = new JLabel("Smart Research Paper Recommendation System");
        titleLabel.setFont(new Font("SansSerif", Font.BOLD, 18));
        titleLabel.setHorizontalAlignment(SwingConstants.CENTER);
        
        JLabel subtitleLabel = new JLabel("KL University - Dept. of CSE");
        subtitleLabel.setFont(new Font("SansSerif", Font.PLAIN, 14));
        subtitleLabel.setHorizontalAlignment(SwingConstants.CENTER);

        gbc.gridx = 0; gbc.gridy = 0; gbc.gridwidth = 2;
        add(titleLabel, gbc);

        gbc.gridy = 1;
        add(subtitleLabel, gbc);

        gbc.gridwidth = 1;
        gbc.gridy = 2; gbc.gridx = 0;
        add(new JLabel("Username:"), gbc);

        gbc.gridx = 1;
        usernameField = new JTextField(15);
        add(usernameField, gbc);

        gbc.gridy = 3; gbc.gridx = 0;
        add(new JLabel("Password:"), gbc);

        gbc.gridx = 1;
        passwordField = new JPasswordField(15);
        add(passwordField, gbc);

        JPanel buttonPanel = new JPanel();
        buttonPanel.setBackground(Color.WHITE);
        JButton loginButton = new JButton("Login");
        loginButton.setBackground(new Color(37, 99, 235));
        loginButton.setForeground(Color.WHITE);
        
        JButton registerButton = new JButton("Register");
        registerButton.setBackground(new Color(219, 234, 254));
        
        buttonPanel.add(loginButton);
        buttonPanel.add(registerButton);

        gbc.gridy = 4; gbc.gridx = 0; gbc.gridwidth = 2;
        add(buttonPanel, gbc);

        statusLabel = new JLabel(" ");
        statusLabel.setForeground(Color.RED);
        statusLabel.setHorizontalAlignment(SwingConstants.CENTER);
        gbc.gridy = 5;
        add(statusLabel, gbc);

        loginButton.addActionListener(e -> {
            String username = usernameField.getText();
            String password = new String(passwordField.getPassword());
            User user = DatabaseManager.authenticateUser(username, password);
            if (user != null) {
                new MainFrame(user).setVisible(true);
                dispose();
            } else {
                statusLabel.setText("Invalid credentials!");
            }
        });

        registerButton.addActionListener(e -> {
            String username = usernameField.getText();
            String password = new String(passwordField.getPassword());
            if (username.isEmpty() || password.isEmpty()) {
                statusLabel.setText("Enter username and password to register.");
                return;
            }
            String interests = JOptionPane.showInputDialog(this, "Enter your interests (comma separated):");
            if (interests != null) {
                User user = DatabaseManager.registerUser(username, password, interests);
                if (user != null) {
                    statusLabel.setText("Registered successfully! You can login now.");
                } else {
                    statusLabel.setText("Registration failed. Username may exist.");
                }
            }
        });
    }
}
