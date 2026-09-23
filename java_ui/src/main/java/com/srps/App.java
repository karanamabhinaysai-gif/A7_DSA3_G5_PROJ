package com.srps;

import com.srps.ui.LoginFrame;
import javax.swing.*;

public class App {
    public static void main(String[] args) {
        Thread.setDefaultUncaughtExceptionHandler((t, e) -> {
            e.printStackTrace();
            JOptionPane.showMessageDialog(null,
                    "An unexpected error occurred: " + e.getMessage(),
                    "Error",
                    JOptionPane.ERROR_MESSAGE);
        });

        SwingUtilities.invokeLater(() -> {
            try {
                UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
            } catch (Exception e) {
                e.printStackTrace();
            }
            new LoginFrame().setVisible(true);
        });
    }
}
