package com.srps.model;

public class Recommendation {
    private Paper paper;
    private double finalScore;
    private double contentScore;
    private double citationScore;
    private double userScore;

    public Recommendation() {}

    public Recommendation(Paper paper, double finalScore, double contentScore, double citationScore, double userScore) {
        this.paper = paper;
        this.finalScore = finalScore;
        this.contentScore = contentScore;
        this.citationScore = citationScore;
        this.userScore = userScore;
    }

    public Paper getPaper() { return paper; }
    public void setPaper(Paper paper) { this.paper = paper; }

    public double getFinalScore() { return finalScore; }
    public void setFinalScore(double finalScore) { this.finalScore = finalScore; }

    public double getContentScore() { return contentScore; }
    public void setContentScore(double contentScore) { this.contentScore = contentScore; }

    public double getCitationScore() { return citationScore; }
    public void setCitationScore(double citationScore) { this.citationScore = citationScore; }

    public double getUserScore() { return userScore; }
    public void setUserScore(double userScore) { this.userScore = userScore; }

    @Override
    public String toString() {
        return "Recommendation{" +
                "paper=" + paper.getTitle() +
                ", finalScore=" + finalScore +
                '}';
    }
}
