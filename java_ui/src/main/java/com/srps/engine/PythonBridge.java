package com.srps.engine;

import com.srps.model.Paper;
import com.srps.model.Recommendation;
import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Bridges Java UI to the Python recommendation engine.
 * Invokes the Python CLI and parses the JSON output.
 */
public class PythonBridge {

    /**
     * Get recommendations by calling the Python engine process.
     *
     * @param query  Search query text
     * @param userId User ID for personalized results
     * @param topK   Number of results to return
     * @return List of Recommendation objects
     */
    public static List<Recommendation> getRecommendations(String query, int userId, int topK) {
        List<Recommendation> recommendations = new ArrayList<>();
        String pythonCmd = System.getProperty("srps.python.cmd", "python");
        String dbPath = System.getProperty("srps.db.path", "database/papers.db");

        // Determine project root (parent of java_ui)
        File projectRoot = new File(System.getProperty("user.dir")).getParentFile();
        if (projectRoot == null || !new File(projectRoot, "python_engine").exists()) {
            // Fallback: try current directory's parent or use a known path
            projectRoot = new File("..").getAbsoluteFile();
        }

        ProcessBuilder pb = new ProcessBuilder(
                pythonCmd, "-m", "python_engine.main",
                "--db", dbPath,
                "--query", query,
                "--user_id", String.valueOf(userId),
                "--top_k", String.valueOf(topK)
        );
        pb.directory(projectRoot);
        pb.redirectErrorStream(false);

        try {
            Process process = pb.start();
            StringBuilder output = new StringBuilder();
            StringBuilder errorOutput = new StringBuilder();

            // Read stdout
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line);
                }
            }

            // Read stderr
            try (BufferedReader errReader = new BufferedReader(new InputStreamReader(process.getErrorStream()))) {
                String errLine;
                while ((errLine = errReader.readLine()) != null) {
                    errorOutput.append(errLine).append("\n");
                }
            }

            boolean finished = process.waitFor(30, TimeUnit.SECONDS);
            if (!finished) {
                process.destroyForcibly();
                System.err.println("Python process timed out.");
                return recommendations;
            }

            if (process.exitValue() != 0) {
                System.err.println("Python process failed (exit code " + process.exitValue() + "):");
                System.err.println(errorOutput.toString());
                return recommendations;
            }

            String jsonOutput = output.toString().trim();
            if (!jsonOutput.isEmpty()) {
                JSONObject response = new JSONObject(jsonOutput);

                // Check for error
                if (response.has("error")) {
                    System.err.println("Python engine error: " + response.getString("error"));
                    return recommendations;
                }

                // Parse results array
                JSONArray results = response.getJSONArray("results");
                for (int i = 0; i < results.length(); i++) {
                    JSONObject obj = results.getJSONObject(i);
                    Paper paper = new Paper(
                            obj.optInt("paper_id"),
                            obj.optString("title", ""),
                            obj.optString("abstract", ""),
                            obj.optString("authors", ""),
                            obj.optInt("year", 0),
                            obj.optString("keywords", ""),
                            obj.optString("venue", ""),
                            ""
                    );
                    Recommendation rec = new Recommendation(
                            paper,
                            obj.optDouble("final_score", 0.0),
                            obj.optDouble("content_score", 0.0),
                            obj.optDouble("citation_score", 0.0),
                            obj.optDouble("user_score", 0.0)
                    );
                    recommendations.add(rec);
                }
            }
        } catch (Exception e) {
            System.err.println("Error calling Python engine: " + e.getMessage());
            e.printStackTrace();
        }

        return recommendations;
    }
}
