package com.srps.ui;

import com.srps.db.DatabaseManager;
import com.srps.model.User;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.util.ArrayList;
import java.util.List;

public class ProfilePanel extends JDialog {
    private User currentUser;
    private String[] topics = {
            "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
            "Data Mining", "Distributed Systems", "Database Systems",
            "Software Engineering", "Computer Networks", "Information Retrieval"
    };
    private List<JCheckBox> topicBoxes = new ArrayList<>();
    private JTextArea interestsArea;

    public ProfilePanel(Frame owner, User user) {
        super(owner, "User Profile", true);
        this.currentUser = user;
        setSize(500, 600);
        setLocationRelativeTo(owner);
        getContentPane().setBackground(Color.WHITE);
        
        initUI();
    }

    private void initUI() {
        setLayout(new BorderLayout(10, 10));
        JPanel contentPanel = new JPanel();
        contentPanel.setLayout(new BoxLayout(contentPanel, BoxLayout.Y_AXIS));
        contentPanel.setBorder(new EmptyBorder(20, 20, 20, 20));
        contentPanel.setBackground(Color.WHITE);

        JLabel userLabel = new JLabel("Username: " + currentUser.getUsername());
        userLabel.setFont(new Font("SansSerif", Font.BOLD, 16));
        contentPanel.add(userLabel);
        contentPanel.add(Box.createRigidArea(new Dimension(0, 20)));

        contentPanel.add(new JLabel("Select Topics of Interest:"));
        JPanel topicsPanel = new JPanel(new GridLayout(5, 2, 5, 5));
        topicsPanel.setBackground(Color.WHITE);
        String currentInterests = currentUser.getInterests() != null ? currentUser.getInterests() : "";
        
        for (String topic : topics) {
            JCheckBox cb = new JCheckBox(topic);
            cb.setBackground(Color.WHITE);
            if (currentInterests.contains(topic)) {
                cb.setSelected(true);
            }
            topicBoxes.add(cb);
            topicsPanel.add(cb);
        }
        contentPanel.add(topicsPanel);
        contentPanel.add(Box.createRigidArea(new Dimension(0, 10)));

        contentPanel.add(new JLabel("Other Interests (comma separated):"));
        interestsArea = new JTextArea(3, 30);
        interestsArea.setText(currentInterests);
        interestsArea.setLineWrap(true);
        contentPanel.add(new JScrollPane(interestsArea));
        contentPanel.add(Box.createRigidArea(new Dimension(0, 20)));
        
        contentPanel.add(new JLabel("Reading History (Paper IDs):"));
        JList<Integer> historyList = new JList<>(DatabaseManager.getUserHistory(currentUser.getId()).toArray(new Integer[0]));
        contentPanel.add(new JScrollPane(historyList));

        add(contentPanel, BorderLayout.CENTER);

        JPanel buttonPanel = new JPanel();
        buttonPanel.setBackground(Color.WHITE);
        JButton saveBtn = new JButton("Save");
        saveBtn.setBackground(new Color(37, 99, 235));
        saveBtn.setForeground(Color.WHITE);
        
        JButton closeBtn = new JButton("Close");
        
        saveBtn.addActionListener(e -> saveProfile());
        closeBtn.addActionListener(e -> dispose());
        
        buttonPanel.add(saveBtn);
        buttonPanel.add(closeBtn);
        add(buttonPanel, BorderLayout.SOUTH);
    }

    private void saveProfile() {
        StringBuilder sb = new StringBuilder();
        for (JCheckBox cb : topicBoxes) {
            if (cb.isSelected()) {
                if (sb.length() > 0) sb.append(", ");
                sb.append(cb.getText());
            }
        }
        String other = interestsArea.getText().trim();
        if (!other.isEmpty()) {
            if (sb.length() > 0) sb.append(", ");
            sb.append(other);
        }
        
        String newInterests = sb.toString();
        currentUser.setInterests(newInterests);
        DatabaseManager.updateUserInterests(currentUser.getId(), newInterests);
        JOptionPane.showMessageDialog(this, "Profile updated successfully!");
        dispose();
    }
}
