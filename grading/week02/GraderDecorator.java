package com.orca.patterns.grading;

/**
 * Grader 데코레이터 추상 클래스
 * Decorator 패턴의 Decorator 역할
 */
public abstract class GraderDecorator implements Grader {

    protected Grader wrappedGrader;

    public GraderDecorator(Grader grader) {
        this.wrappedGrader = grader;
    }

    @Override
    public GradeResult grade(String studentPackage) {
        // 기본적으로 래핑된 grader의 결과를 반환
        // 구체적인 데코레이터에서 추가적인 검증 수행
        return wrappedGrader.grade(studentPackage);
    }

    @Override
    public String getGradingCategory() {
        // 구체적인 데코레이터에서 오버라이드
        return "Base Decorator";
    }

    /**
     * 이전 결과와 새로운 결과를 합치는 유틸리티 메소드
     */
    protected GradeResult mergeResults(GradeResult previousResult, GradeResult newResult) {
        // 이전 결과의 모든 테스트와 세부사항을 새로운 결과에 추가
        for (String detail : previousResult.getDetails()) {
            newResult.addDetail(detail);
        }

        // 테스트 결과 통합 (이전 결과의 실패가 있으면 최종 결과도 실패)
        if (!previousResult.isPassed()) {
            newResult.addTest(false, "Previous grading step failed");
        }

        return newResult;
    }
}