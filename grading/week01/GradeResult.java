package com.orca.patterns.grading;

import java.util.ArrayList;
import java.util.List;

/**
 * 채점 결과를 저장하는 클래스
 */
public class GradeResult {
    private boolean passed;
    private int totalTests;
    private int passedTests;
    private final List<String> successMessages;
    private final List<String> failureMessages;
    private final List<String> details;

    public GradeResult() {
        this.passed = true;
        this.totalTests = 0;
        this.passedTests = 0;
        this.successMessages = new ArrayList<>();
        this.failureMessages = new ArrayList<>();
        this.details = new ArrayList<>();
    }

    public void addTest(boolean testPassed, String message) {
        totalTests++;
        if (testPassed) {
            passedTests++;
            successMessages.add(message);
        } else {
            passed = false;
            failureMessages.add(message);
        }
        details.add((testPassed ? "[PASS] " : "[FAIL] ") + message);
    }

    public void addDetail(String detail) {
        details.add("[INFO] " + detail);
    }

    // Getters
    public boolean isPassed() { return passed; }
    public int getTotalTests() { return totalTests; }
    public int getPassedTests() { return passedTests; }
    public List<String> getSuccessMessages() { return new ArrayList<>(successMessages); }
    public List<String> getFailureMessages() { return new ArrayList<>(failureMessages); }
    public List<String> getDetails() { return new ArrayList<>(details); }

    public double getScore() {
        return totalTests == 0 ? 0.0 : (double) passedTests / totalTests * 100;
    }

    @Override
    public String toString() {
        return String.format("GradeResult{passed=%s, score=%.1f%%, tests=%d/%d}",
                           passed, getScore(), passedTests, totalTests);
    }
}