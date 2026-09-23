package com.srps.model;

public class Paper {
    private int id;
    private String title;
    private String abstractText;
    private String authors;
    private int year;
    private String keywords;
    private String venue;
    private String doi;

    public Paper() {}

    public Paper(int id, String title, String abstractText, String authors, int year, String keywords, String venue, String doi) {
        this.id = id;
        this.title = title;
        this.abstractText = abstractText;
        this.authors = authors;
        this.year = year;
        this.keywords = keywords;
        this.venue = venue;
        this.doi = doi;
    }

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }

    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }

    public String getAbstractText() { return abstractText; }
    public void setAbstractText(String abstractText) { this.abstractText = abstractText; }

    public String getAuthors() { return authors; }
    public void setAuthors(String authors) { this.authors = authors; }

    public int getYear() { return year; }
    public void setYear(int year) { this.year = year; }

    public String getKeywords() { return keywords; }
    public void setKeywords(String keywords) { this.keywords = keywords; }

    public String getVenue() { return venue; }
    public void setVenue(String venue) { this.venue = venue; }

    public String getDoi() { return doi; }
    public void setDoi(String doi) { this.doi = doi; }

    @Override
    public String toString() {
        return "Paper{" +
                "id=" + id +
                ", title='" + title + '\'' +
                ", authors='" + authors + '\'' +
                ", year=" + year +
                '}';
    }
}
