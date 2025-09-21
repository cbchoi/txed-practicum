package com.orca.patterns.grading;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.Date;

/**
 * 채점 결과 파일 생성기
 * 채점 결과를 다양한 형태의 파일로 출력
 */
public class ResultFileGenerator {

    private static final String RESULT_FILE_NAME = "week2_grading_result.txt";
    private static final String PASS_FILE_NAME = "PASS";
    private static final String FAIL_FILE_NAME = "FAIL";

    /**
     * 채점 결과 파일들을 생성
     * @param result 채점 결과
     * @param outputDirectory 출력 디렉토리 (null이면 현재 디렉토리)
     * @throws IOException 파일 생성 실패 시
     */
    public void generateResultFile(GradeResult result, String outputDirectory) throws IOException {
        String baseDir = outputDirectory != null ? outputDirectory : ".";
        File outputDir = new File(baseDir);

        if (!outputDir.exists()) {
            outputDir.mkdirs();
        }

        // 1. 상세 결과 파일 생성
        generateDetailedResultFile(result, outputDir);

        // 2. PASS/FAIL 파일 생성
        generatePassFailFile(result, outputDir);
    }

    /**
     * 상세 채점 결과 파일 생성
     */
    private void generateDetailedResultFile(GradeResult result, File outputDir) throws IOException {
        File resultFile = new File(outputDir, RESULT_FILE_NAME);

        try (PrintWriter writer = new PrintWriter(new FileWriter(resultFile))) {
            writer.println("======================================");
            writer.println("Week 2: Behavioral Patterns 채점 결과");
            writer.println("======================================");
            writer.println("채점 일시: " + new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));
            writer.println("최종 결과: " + (result.isPassed() ? "PASS" : "FAIL"));
            writer.println("총 테스트: " + result.getTotalTests());
            writer.println("통과 테스트: " + result.getPassedTests());
            writer.println("실패 테스트: " + result.getFailedTests());
            writer.println("통과율: " + String.format("%.1f%%", result.getPassRate()));
            writer.println();

            writer.println("=== 테스트 결과 상세 ===");
            for (int i = 0; i < result.getTestResults().size(); i++) {
                Boolean testResult = result.getTestResults().get(i);
                String testDescription = result.getTestDescriptions().get(i);
                writer.println(String.format("[%s] %s",
                    testResult ? "PASS" : "FAIL", testDescription));
            }

            writer.println();
            writer.println("=== 채점 세부 사항 ===");
            for (String detail : result.getDetails()) {
                writer.println("- " + detail);
            }

            writer.println();
            writer.println("=== 채점 기준 ===");
            writer.println("1. Observer Pattern (40점):");
            writer.println("   - EventObserver 인터페이스 정의");
            writer.println("   - ProcessEvent 데이터 클래스");
            writer.println("   - EventPublisher Subject 구현");
            writer.println("   - LoggingObserver, AlertingObserver 구현체");

            writer.println();
            writer.println("2. Command Pattern (40점):");
            writer.println("   - Command 인터페이스 정의");
            writer.println("   - ProcessCommand 구체 구현");
            writer.println("   - CommandInvoker 실행 관리자");
            writer.println("   - 실행/취소 기능");

            writer.println();
            writer.println("3. 통합 및 구현 (20점):");
            writer.println("   - Observer-Command 연동");
            writer.println("   - 메인 클래스 및 시나리오");
            writer.println("   - 종합적인 구현 완성도");

            writer.println();
            if (result.isPassed()) {
                writer.println("축하합니다! Week 2 Behavioral Patterns 과제를 성공적으로 완료하셨습니다.");
                writer.println("Observer Pattern과 Command Pattern의 핵심 개념을 잘 이해하고 구현하셨습니다.");
            } else {
                writer.println("아쉽게도 일부 요구사항이 충족되지 않았습니다.");
                writer.println("위의 실패한 테스트들을 참고하여 코드를 수정해 주세요.");
                writer.println("특히 인터페이스 정의와 패턴 구현에 집중해 주세요.");
            }
        }
    }

    /**
     * PASS/FAIL 파일 생성
     */
    private void generatePassFailFile(GradeResult result, File outputDir) throws IOException {
        String fileName = result.isPassed() ? PASS_FILE_NAME : FAIL_FILE_NAME;
        File passFailFile = new File(outputDir, fileName);

        try (PrintWriter writer = new PrintWriter(new FileWriter(passFailFile))) {
            writer.println("Week 2: Behavioral Patterns 채점 결과");
            writer.println("결과: " + (result.isPassed() ? "PASS" : "FAIL"));
            writer.println("통과율: " + String.format("%.1f%%", result.getPassRate()));
            writer.println("채점 일시: " + new SimpleDateFormat("yyyy-MM-dd HH:mm:ss").format(new Date()));

            if (!result.isPassed()) {
                writer.println();
                writer.println("실패한 테스트:");
                for (int i = 0; i < result.getTestResults().size(); i++) {
                    if (!result.getTestResults().get(i)) {
                        writer.println("- " + result.getTestDescriptions().get(i));
                    }
                }
            }
        }
    }

    /**
     * 콘솔에 채점 결과 요약 출력
     */
    public void printSummary(GradeResult result) {
        System.out.println("\n" + "=".repeat(50));
        System.out.println("Week 2: Behavioral Patterns 채점 완료");
        System.out.println("=".repeat(50));
        System.out.println("최종 결과: " + (result.isPassed() ? "✅ PASS" : "❌ FAIL"));
        System.out.println("통과율: " + String.format("%.1f%%", result.getPassRate()) +
                         String.format(" (%d/%d)", result.getPassedTests(), result.getTotalTests()));

        if (result.isPassed()) {
            System.out.println("\n🎉 축하합니다! Behavioral Patterns 구현을 성공적으로 완료하셨습니다!");
            System.out.println("📚 Observer Pattern과 Command Pattern의 핵심을 잘 이해하셨습니다.");
        } else {
            System.out.println("\n📋 일부 요구사항을 다시 확인해 주세요:");
            int failCount = 0;
            for (int i = 0; i < result.getTestResults().size() && failCount < 3; i++) {
                if (!result.getTestResults().get(i)) {
                    System.out.println("   ❌ " + result.getTestDescriptions().get(i));
                    failCount++;
                }
            }
            if (result.getFailedTests() > 3) {
                System.out.println("   ... 그 외 " + (result.getFailedTests() - 3) + "개 항목");
            }
        }

        System.out.println("\n📄 상세 결과는 " + RESULT_FILE_NAME + " 파일을 확인해 주세요.");
        System.out.println("=".repeat(50));
    }

    /**
     * 개발자용 디버그 정보 출력
     */
    public void printDebugInfo(GradeResult result) {
        System.out.println("\n=== DEBUG INFO ===");
        System.out.println("Total tests: " + result.getTotalTests());
        System.out.println("Passed tests: " + result.getPassedTests());
        System.out.println("Failed tests: " + result.getFailedTests());
        System.out.println("Pass rate: " + result.getPassRate() + "%");

        System.out.println("\nTest details:");
        for (int i = 0; i < result.getTestResults().size(); i++) {
            System.out.println(String.format("  %d. [%s] %s",
                i + 1,
                result.getTestResults().get(i) ? "PASS" : "FAIL",
                result.getTestDescriptions().get(i)
            ));
        }

        System.out.println("\nGrading details:");
        for (String detail : result.getDetails()) {
            System.out.println("  - " + detail);
        }
    }
}