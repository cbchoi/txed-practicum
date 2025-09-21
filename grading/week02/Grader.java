package com.orca.patterns.grading;

/**
 * Week 2 Behavioral Patterns 채점기 인터페이스
 * Decorator Pattern의 기본 구성 요소
 */
public interface Grader {

    /**
     * 학생 코드에 대한 채점 수행
     * @param studentPackage 학생이 작성한 코드의 패키지 경로
     * @return 채점 결과
     */
    GradeResult grade(String studentPackage);

    /**
     * 채점 카테고리 반환
     * @return 채점 카테고리 설명
     */
    String getGradingCategory();
}