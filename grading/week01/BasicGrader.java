package com.orca.patterns.grading;

/**
 * 기본 채점 구현체
 * Decorator 패턴의 ConcreteComponent 역할
 */
public class BasicGrader implements Grader {

    @Override
    public GradeResult grade(String studentPackage) {
        GradeResult result = new GradeResult();
        result.addDetail("Starting basic grading for package: " + studentPackage);

        // 기본적인 패키지 존재 여부만 확인
        try {
            // 패키지가 유효한지 확인하는 기본 검증
            if (studentPackage == null || studentPackage.trim().isEmpty()) {
                result.addTest(false, "Invalid package name provided");
            } else {
                result.addTest(true, "Package name is valid");
                result.addDetail("Package validation completed");
            }
        } catch (Exception e) {
            result.addTest(false, "Error during basic validation: " + e.getMessage());
        }

        return result;
    }

    @Override
    public String getGradingCategory() {
        return "Basic Validation";
    }
}