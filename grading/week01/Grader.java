package com.orca.patterns.grading;

/**
 * 채점을 수행하는 기본 인터페이스
 * Decorator 패턴의 Component 역할
 */
public interface Grader {

    /**
     * 채점을 수행하고 결과를 반환
     * @param studentPackage 학생이 작성한 코드의 패키지 경로
     * @return 채점 결과
     */
    GradeResult grade(String studentPackage);

    /**
     * 채점 항목의 이름 반환
     * @return 채점 항목 이름
     */
    String getGradingCategory();
}