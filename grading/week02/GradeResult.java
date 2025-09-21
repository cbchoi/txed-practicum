package com.orca.patterns.grading;

import java.util.ArrayList;
import java.util.List;

/**
 * 채점 결과를 나타내는 클래스
 * 각 테스트 케이스의 결과와 세부 정보를 저장
 */
public class GradeResult {

    private final List<TestResult> testResults;
    private final List<String> details;
    private int totalTests;
    private int passedTests;
    private long gradingStartTime;
    private long gradingEndTime;

    public GradeResult() {
        this.testResults = new ArrayList<>();
        this.details = new ArrayList<>();
        this.totalTests = 0;
        this.passedTests = 0;
        this.gradingStartTime = System.currentTimeMillis();
    }

    /**
     * 테스트 결과 추가
     * @param passed 통과 여부
     * @param description 테스트 설명
     */
    public void addTest(boolean passed, String description) {
        testResults.add(new TestResult(passed, description));
        totalTests++;
        if (passed) {
            passedTests++;
        }
    }

    /**
     * 테스트 결과 추가 (점수 포함)
     * @param passed 통과 여부
     * @param description 테스트 설명
     * @param points 획득 점수
     * @param maxPoints 만점
     */
    public void addTest(boolean passed, String description, int points, int maxPoints) {
        TestResult result = new TestResult(passed, description);
        result.setPoints(points);
        result.setMaxPoints(maxPoints);
        testResults.add(result);
        totalTests++;
        if (passed) {
            passedTests++;
        }
    }

    /**
     * 세부 정보 추가
     * @param detail 세부 정보
     */
    public void addDetail(String detail) {
        details.add(detail);
    }

    /**
     * 채점 완료 시점 기록
     */
    public void completeGrading() {
        this.gradingEndTime = System.currentTimeMillis();
    }

    // Getters
    public List<TestResult> getTestResults() {
        return new ArrayList<>(testResults);
    }

    public List<String> getDetails() {
        return new ArrayList<>(details);
    }

    public int getTotalTests() {
        return totalTests;
    }

    public int getPassedTests() {
        return passedTests;
    }

    public boolean isPassed() {
        return passedTests == totalTests && totalTests > 0;
    }

    public double getPassPercentage() {
        return totalTests > 0 ? (double) passedTests / totalTests * 100 : 0;
    }

    public long getGradingDuration() {
        return gradingEndTime - gradingStartTime;
    }

    public int getTotalPoints() {
        return testResults.stream()
                .mapToInt(TestResult::getPoints)
                .sum();
    }

    public int getMaxTotalPoints() {
        return testResults.stream()
                .mapToInt(TestResult::getMaxPoints)
                .sum();
    }

    @Override
    public String toString() {
        return String.format("GradeResult{passed: %d/%d (%.1f%%), duration: %dms}",
                passedTests, totalTests, getPassPercentage(), getGradingDuration());
    }

    /**
     * 개별 테스트 결과를 나타내는 내부 클래스
     */
    public static class TestResult {
        private final boolean passed;
        private final String description;
        private final long timestamp;
        private int points = 0;
        private int maxPoints = 0;

        public TestResult(boolean passed, String description) {
            this.passed = passed;
            this.description = description;
            this.timestamp = System.currentTimeMillis();
        }

        // Getters and Setters
        public boolean isPassed() { return passed; }
        public String getDescription() { return description; }
        public long getTimestamp() { return timestamp; }
        public int getPoints() { return points; }
        public void setPoints(int points) { this.points = points; }
        public int getMaxPoints() { return maxPoints; }
        public void setMaxPoints(int maxPoints) { this.maxPoints = maxPoints; }

        @Override
        public String toString() {
            return String.format("[%s] %s", passed ? "PASS" : "FAIL", description);
        }
    }
}