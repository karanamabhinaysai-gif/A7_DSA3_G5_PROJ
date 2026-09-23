package com.srps.ui;

import com.srps.engine.PythonBridge;
import com.srps.model.Recommendation;
import com.srps.model.User;

import javax.swing.*;
import java.awt.*;
import java.util.List;

public class MainFrame extends JFrame {
    private User currentUser;
    private ResultsPanel resultsPanel;
    private JTextField searchField;
    private JSpinner topKSpinner;
    private JLabel statusLabel;

    public MainFrame(User user) {
        this.currentUser = user;
        setTitle("Dashboard - Smart Research Paper Recommendation System");
        setSize(900, 700);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        getContentPane().setBackground(new Color(243, 244, 246));

        initUI();
    }

    private void initUI() {
        setLayout(new BorderLayout());

        JPanel topBar = new JPanel(new BorderLayout());
        topBar.setBackground(Color.WHITE);
        topBar.setBorder(BorderFactory.createEmptyBorder(10, 20, 10, 20));

        JLabel welcomeLabel = new JLabel("Welcome, " + currentUser.getUsername());
        welcomeLabel.setFont(new Font("SansSerif", Font.BOLD, 14));
        topBar.add(welcomeLabel, BorderLayout.WEST);

        JPanel actionPanel = new JPanel();
        actionPanel.setBackground(Color.WHITE);
        JButton profileBtn = new JButton("Profile");
        JButton logoutBtn = new JButton("Logout");
        
        profileBtn.addActionListener(e -> new ProfilePanel(this, currentUser).setVisible(true));
        logoutBtn.addActionListener(e -> {
            new LoginFrame().setVisible(true);
            dispose();
        });
        
        actionPanel.add(profileBtn);
        actionPanel.add(logoutBtn);
        topBar.add(actionPanel, BorderLayout.EAST);

        add(topBar, BorderLayout.NORTH);

        JPanel centerPanel = new JPanel(new BorderLayout());
        
        JPanel searchPanel = new JPanel(new FlowLayout(FlowLayout.CENTER, 10, 10));
        searchField = new JTextField(40);
        JButton searchBtn = new JButton("Search");
        searchBtn.setBackground(new Color(37, 99, 235));
        searchBtn.setForeground(Color.WHITE);
        
        topKSpinner = new JSpinner(new SpinnerNumberModel(10, 1, 50, 1));
        
        searchPanel.add(new JLabel("Query:"));
        searchPanel.add(searchField);
        searchPanel.add(new JLabel("Top-K:"));
        searchPanel.add(topKSpinner);
        searchPanel.add(searchBtn);

        centerPanel.add(searchPanel, BorderLayout.NORTH);

        resultsPanel = new ResultsPanel(currentUser);
        JScrollPane scrollPane = new JScrollPane(resultsPanel);
        scrollPane.getVerticalScrollBar().setUnitIncrement(16);
        centerPanel.add(scrollPane, BorderLayout.CENTER);

        add(centerPanel, BorderLayout.CENTER);

        statusLabel = new JLabel(" Ready");
        statusLabel.setBorder(BorderFactory.createEmptyBorder(5, 5, 5, 5));
        add(statusLabel, BorderLayout.SOUTH);

        searchBtn.addActionListener(e -> performSearch());
        searchField.addActionListener(e -> performSearch());
    }

    private void performSearch() {
        String query = searchField.getText().trim();
        if (query.isEmpty()) return;

        int topK = (Integer) topKSpinner.getValue();
        statusLabel.setText(" Searching...");
        resultsPanel.clearResults();
        resultsPanel.add(new JLabel("Loading..."));
        resultsPanel.revalidate();
        resultsPanel.repaint();

        SwingWorker<List<Recommendation>, Void> worker = new SwingWorker<>() {
            @Override
            protected List<Recommendation> doInBackground() {
                return PythonBridge.getRecommendations(query, currentUser.getId(), topK);
            }

            @Override
            protected void done() {
                try {
                    List<Recommendation> recs = get();
                    resultsPanel.setRecommendations(recs);
                    statusLabel.setText(" Found " + recs.size() + " results.");
                } catch (Exception ex) {
                    ex.printStackTrace();
                    statusLabel.setText(" Error during search.");
                    JOptionPane.showMessageDialog(MainFrame.this, "Error: " + ex.getMessage());
                }
            }
        };
        worker.execute();
    }
}
