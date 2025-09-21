package com.orca.patterns.grading;

/**
 * 채점 데코레이터의 기본 추상 클래스
 * Decorator 패턴의 Decorator 역할
 */
public abstract class GraderDecorator implements Grader {

    protected final Grader grader;

    public GraderDecorator(Grader grader) {
        if (grader == null) {
            throw new IllegalArgumentException("Grader cannot be null");
        }
        this.grader = grader;
    }

    @Override
    public GradeResult grade(String studentPackage) {
        // 기존 채점 결과를 가져옴
        GradeResult result = grader.grade(studentPackage);

        // 추가적인 채점 수행
        GradeResult additionalResult = performAdditionalGrading(studentPackage);

        // 결과를 병합
        return mergeResults(result, additionalResult);
    }

    /**
     * 추가적인 채점을 수행하는 메소드
     * 하위 클래스에서 구현해야 함
     * @param studentPackage 학생 패키지 경로
     * @return 추가 채점 결과
     */
    protected abstract GradeResult performAdditionalGrading(String studentPackage);

    /**
     * 두 채점 결과를 병합
     * @param original 기존 결과
     * @param additional 추가 결과
     * @return 병합된 결과
     */
    protected GradeResult mergeResults(GradeResult original, GradeResult additional) {
        GradeResult merged = new GradeResult();

        // 기존 결과의 모든 정보 복사
        for (String detail : original.getDetails()) {
            merged.getDetails().add(detail);
        }

        // 기존 테스트 결과 복사
        for (String success : original.getSuccessMessages()) {
            merged.addTest(true, success);
        }
        for (String failure : original.getFailureMessages()) {
            merged.addTest(false, failure);
        }

        // 추가 결과 병합
        for (String success : additional.getSuccessMessages()) {
            merged.addTest(true, success);
        }
        for (String failure : additional.getFailureMessages()) {
            merged.addTest(false, failure);
        }

        // 추가 상세 정보 병합
        for (String detail : additional.getDetails()) {
            merged.getDetails().add(detail);
        }

        return merged;
    }

    @Override
    public String getGradingCategory() {
        return grader.getGradingCategory() + " + " + getAdditionalCategory();
    }

    /**
     * 추가 채점 카테고리 이름 반환
     * @return 카테고리 이름
     */
    protected abstract String getAdditionalCategory();
}