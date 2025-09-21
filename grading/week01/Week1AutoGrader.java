package com.orca.patterns.grading;

import java.io.IOException;

/**
 * Week 1 Creational Patterns 자동 채점기
 * Decorator Pattern을 사용하여 다양한 채점 기준을 조합
 */
public class Week1AutoGrader {

    private static final String DEFAULT_STUDENT_PACKAGE = "com.orca.patterns";

    public static void main(String[] args) {
        String studentPackage = DEFAULT_STUDENT_PACKAGE;
        String outputDirectory = null;

        // 명령행 인자 처리
        if (args.length > 0) {
            studentPackage = args[0];
        }
        if (args.length > 1) {
            outputDirectory = args[1];
        }

        System.out.println("Week 1 Creational Patterns Auto-Grader");
        System.out.println("======================================");
        System.out.println("Student Package: " + studentPackage);
        System.out.println("Output Directory: " + (outputDirectory != null ? outputDirectory : "current directory"));
        System.out.println();

        try {
            // 채점 실행
            Week1AutoGrader grader = new Week1AutoGrader();
            GradeResult result = grader.grade(studentPackage);

            // 결과 파일 생성
            ResultFileGenerator generator = new ResultFileGenerator();
            generator.generateResultFile(result, outputDirectory);
            generator.printSummary(result);

            // 프로그램 종료 코드 설정
            System.exit(result.isPassed() ? 0 : 1);

        } catch (Exception e) {
            System.err.println("Grading failed with exception: " + e.getMessage());
            e.printStackTrace();

            // 예외 발생 시 fail 파일 생성
            try {
                createFailFileForException(e, outputDirectory);
            } catch (IOException ioException) {
                System.err.println("Could not create fail file: " + ioException.getMessage());
            }

            System.exit(1);
        }
    }

    /**
     * Decorator Pattern을 사용하여 모든 채점 기준을 조합하고 채점을 수행
     * @param studentPackage 학생이 작성한 코드의 패키지 경로
     * @return 종합 채점 결과
     */
    public GradeResult grade(String studentPackage) {
        System.out.println("Starting comprehensive grading...\n");

        // Decorator Pattern 적용: 기본 채점기에 각종 패턴 검증 데코레이터를 중첩 적용
        Grader grader = buildGraderChain();

        // 채점 실행
        GradeResult result = grader.grade(studentPackage);

        System.out.println("\nGrading completed!");
        System.out.println("Category: " + grader.getGradingCategory());

        return result;
    }

    /**
     * Decorator Pattern을 사용하여 채점기 체인 구성
     * 각 데코레이터는 이전 데코레이터의 결과에 추가적인 검증을 수행
     * @return 완전히 구성된 채점기
     */
    private Grader buildGraderChain() {
        // 1. 기본 채점기로 시작
        Grader grader = new BasicGrader();

        // 2. Factory Pattern 검증 데코레이터 추가
        grader = new FactoryPatternGrader(grader);

        // 3. Singleton Pattern 검증 데코레이터 추가
        grader = new SingletonPatternGrader(grader);

        // 4. 통합 테스트 데코레이터 추가
        grader = new IntegrationGrader(grader);

        return grader;
    }

    /**
     * 다양한 조합의 채점기를 생성하는 팩토리 메소드들
     * 필요에 따라 특정 패턴만 검증하거나 단계별로 검증 가능
     */
    public static class GraderBuilder {

        /**
         * Factory Pattern만 검증하는 채점기 생성
         */
        public static Grader createFactoryOnlyGrader() {
            return new FactoryPatternGrader(new BasicGrader());
        }

        /**
         * Singleton Pattern만 검증하는 채점기 생성
         */
        public static Grader createSingletonOnlyGrader() {
            return new SingletonPatternGrader(new BasicGrader());
        }

        /**
         * 통합 테스트만 수행하는 채점기 생성 (Factory와 Singleton이 모두 구현되어 있다고 가정)
         */
        public static Grader createIntegrationOnlyGrader() {
            return new IntegrationGrader(new BasicGrader());
        }

        /**
         * Factory와 Singleton만 검증하는 채점기 생성 (통합 테스트 제외)
         */
        public static Grader createPatternsOnlyGrader() {
            Grader grader = new BasicGrader();
            grader = new FactoryPatternGrader(grader);
            grader = new SingletonPatternGrader(grader);
            return grader;
        }

        /**
         * 전체 검증을 수행하는 채점기 생성 (메인과 동일)
         */
        public static Grader createFullGrader() {
            Grader grader = new BasicGrader();
            grader = new FactoryPatternGrader(grader);
            grader = new SingletonPatternGrader(grader);
            grader = new IntegrationGrader(grader);
            return grader;
        }
    }

    /**
     * 예외 발생 시 실패 파일 생성
     * @param exception 발생한 예외
     * @param outputDirectory 출력 디렉토리
     * @throws IOException 파일 생성 실패 시
     */
    private static void createFailFileForException(Exception exception, String outputDirectory) throws IOException {
        GradeResult failResult = new GradeResult();
        failResult.addTest(false, "Grading failed due to exception: " + exception.getClass().getSimpleName());
        failResult.addTest(false, "Exception message: " + exception.getMessage());
        failResult.addDetail("Exception occurred during grading process");
        failResult.addDetail("This usually indicates missing classes or incorrect package structure");
        failResult.addDetail("Please ensure all required classes exist in the correct package");

        ResultFileGenerator generator = new ResultFileGenerator();
        generator.generateResultFile(failResult, outputDirectory);
    }

    /**
     * 사용법 출력
     */
    public static void printUsage() {
        System.out.println("Usage: java com.orca.patterns.grading.Week1AutoGrader [student_package] [output_directory]");
        System.out.println();
        System.out.println("Arguments:");
        System.out.println("  student_package   - Package containing student's implementation (default: com.orca.patterns)");
        System.out.println("  output_directory  - Directory to save result files (default: current directory)");
        System.out.println();
        System.out.println("Examples:");
        System.out.println("  java com.orca.patterns.grading.Week1AutoGrader");
        System.out.println("  java com.orca.patterns.grading.Week1AutoGrader com.student.solution");
        System.out.println("  java com.orca.patterns.grading.Week1AutoGrader com.student.solution ./results");
        System.out.println();
        System.out.println("Expected classes in student package:");
        System.out.println("  - Processor (interface)");
        System.out.println("  - ProcessorFactory (class)");
        System.out.println("  - NodeManager (class)");
        System.out.println("  - At least 3 Processor implementations");
    }

    /**
     * 개발/테스트용 메소드: 특정 패키지에 대해 단계별 채점 수행
     * @param studentPackage 학생 패키지
     */
    public static void performSteppedGrading(String studentPackage) {
        System.out.println("=== STEPPED GRADING MODE ===\n");

        try {
            // 1단계: Factory Pattern만
            System.out.println("Step 1: Factory Pattern Grading");
            System.out.println("-".repeat(40));
            Grader factoryGrader = GraderBuilder.createFactoryOnlyGrader();
            GradeResult factoryResult = factoryGrader.grade(studentPackage);
            System.out.println("Factory Result: " + factoryResult);
            System.out.println();

            // 2단계: Singleton Pattern만
            System.out.println("Step 2: Singleton Pattern Grading");
            System.out.println("-".repeat(40));
            Grader singletonGrader = GraderBuilder.createSingletonOnlyGrader();
            GradeResult singletonResult = singletonGrader.grade(studentPackage);
            System.out.println("Singleton Result: " + singletonResult);
            System.out.println();

            // 3단계: 통합 테스트
            System.out.println("Step 3: Integration Testing");
            System.out.println("-".repeat(40));
            Grader integrationGrader = GraderBuilder.createIntegrationOnlyGrader();
            GradeResult integrationResult = integrationGrader.grade(studentPackage);
            System.out.println("Integration Result: " + integrationResult);
            System.out.println();

            // 4단계: 전체 테스트
            System.out.println("Step 4: Full Grading");
            System.out.println("-".repeat(40));
            Grader fullGrader = GraderBuilder.createFullGrader();
            GradeResult fullResult = fullGrader.grade(studentPackage);
            System.out.println("Full Result: " + fullResult);

        } catch (Exception e) {
            System.err.println("Stepped grading failed: " + e.getMessage());
        }
    }
}