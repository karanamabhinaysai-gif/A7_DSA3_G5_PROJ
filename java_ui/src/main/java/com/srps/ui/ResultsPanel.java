package com.srps.ui;

import com.srps.db.DatabaseManager;
import com.srps.model.Recommendation;
import com.srps.model.User;

import javax.swing.*;
import javax.swing.border.EmptyBorder;
import java.awt.*;
import java.util.List;

public class ResultsPanel extends JPanel {
    private User currentUser;

    public ResultsPanel(User currentUser) {
        this.currentUser = currentUser;
        setLayout(new BoxLayout(this, BoxLayout.Y_AXIS));
        setBackground(Color.WHITE);
        clearResults();
    }

    public void clearResults() {
        removeAll();
        JLabel msg = new JLabel("Enter a search query to get recommendations");
        msg.setAlignmentX(Component.CENTER_ALIGNMENT);
        msg.setBorder(new EmptyBorder(20, 0, 0, 0));
        add(msg);
        revalidate();
        repaint();
    }

    public void setRecommendations(List<Recommendation> recs) {
        removeAll();
        if (recs == null || recs.isEmpty()) {
            JLabel msg = new JLabel("No results found.");
            msg.setAlignmentX(Component.CENTER_ALIGNMENT);
            msg.setBorder(new EmptyBorder(20, 0, 0, 0));
            add(msg);
        } else {
            int rank = 1;
            for (Recommendation r : recs) {
                add(createCard(r, rank++));
                add(Box.createRigidArea(new Dimension(0, 10)));
            }
        }
        revalidate();
        repaint();
    }

    private JPanel createCard(Recommendation r, int rank) {
        JPanel card = new JPanel(new BorderLayout());
        card.setBackground(Color.WHITE);
        card.setBorder(BorderFactory.createCompoundBorder(
                BorderFactory.createLineBorder(new Color(229, 231, 235), 1, true),
                new EmptyBorder(15, 15, 15, 15)
        ));
        card.setMaximumSize(new Dimension(800, 200));

        JLabel title = new JLabel(rank + ". " + r.getPaper().getTitle());
        title.setFont(new Font("SansSerif", Font.BOLD, 14));
        card.add(title, BorderLayout.NORTH);

        JPanel centerPanel = new JPanel();
        centerPanel.setLayout(new BoxLayout(centerPanel, BoxLayout.Y_AXIS));
        centerPanel.setBackground(Color.WHITE);
        
        JLabel authors = new JLabel("Authors: " + r.getPaper().getAuthors() + " | Year: " + r.getPaper().getYear());
        authors.setForeground(Color.DARK_GRAY);
        JLabel venue = new JLabel("Venue: " + r.getPaper().getVenue());
        venue.setForeground(Color.DARK_GRAY);
        
        String abstractText = r.getPaper().getAbstractText();
        if (abstractText != null && abstractText.length() > 200) {
            abstractText = abstractText.substring(0, 200) + "...";
        }
        JLabel abs = new JLabel("<html><p style='width: 600px;'>" + abstractText + "</p></html>");
        
        String scoreStr = String.format("Overall: %.2f | Content: %.2f | Citation: %.2f | Interest: %.2f",
                r.getFinalScore(), r.getContentScore(), r.getCitationScore(), r.getUserScore());
        JLabel scores = new JLabel(scoreStr);
        scores.setFont(new Font("SansSerif", Font.BOLD, 12));
        
        Color scoreColor = Color.RED;
        if (r.getFinalScore() > 0.7) scoreColor = new Color(34, 197, 94);
        else if (r.getFinalScore() > 0.4) scoreColor = new Color(234, 179, 8);
        scores.setForeground(scoreColor);

        centerPanel.add(authors);
        centerPanel.add(venue);
        centerPanel.add(Box.createRigidArea(new Dimension(0, 5)));
        centerPanel.add(abs);
        centerPanel.add(Box.createRigidArea(new Dimension(0, 5)));
        centerPanel.add(scores);

        card.add(centerPanel, BorderLayout.CENTER);

        JButton saveBtn = new JButton("Save");
        saveBtn.setBackground(new Color(219, 234, 254));
        saveBtn.addActionListener(e -> {
            DatabaseManager.addUserHistory(currentUser.getId(), r.getPaper().getId(), "SAVE");
            JOptionPane.showMessageDialog(this, "Paper saved to history!");
        });
        
        JPanel eastPanel = new JPanel(new BorderLayout());
        eastPanel.setBackground(Color.WHITE);
        eastPanel.add(saveBtn, BorderLayout.NORTH);
        card.add(eastPanel, BorderLayout.EAST);

        return card;
    }
}
