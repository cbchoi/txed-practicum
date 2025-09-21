package com.orca.patterns.grading;

import java.io.*;
import java.nio.file.*;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;

/**
 * 채점 결과를 파일로 생성하는 클래스
 * results.pass 또는 results.fail 파일을 생성하며 상세한 채점 내용을 포함
 */
public class ResultFileGenerator {

    private static final String PASS_FILE = "results.pass";
    private static final String FAIL_FILE = "results.fail";
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    /**
     * 채점 결과를 기반으로 결과 파일을 생성
     * @param result 채점 결과
     * @param outputDirectory 출력 디렉토리 (null이면 현재 디렉토리)
     * @throws IOException 파일 생성 실패 시
     */
    public void generateResultFile(GradeResult result, String outputDirectory) throws IOException {
        String fileName = result.isPassed() ? PASS_FILE : FAIL_FILE;
        Path outputPath;

        if (outputDirectory != null && !outputDirectory.trim().isEmpty()) {
            outputPath = Paths.get(outputDirectory, fileName);
        } else {
            outputPath = Paths.get(fileName);
        }

        // 기존 결과 파일들 정리
        cleanupOldResultFiles(outputPath.getParent());

        String content = generateFileContent(result);

        // 파일 생성
        try (BufferedWriter writer = Files.newBufferedWriter(outputPath, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING)) {
            writer.write(content);
        }

        System.out.println("Result file generated: " + outputPath.toAbsolutePath());
    }

    /**
     * 기존 결과 파일들을 정리 (pass와 fail 파일 모두 삭제)
     * @param directory 정리할 디렉토리
     */
    private void cleanupOldResultFiles(Path directory) {
        if (directory == null) {
            directory = Paths.get(".");
        }

        try {
            Files.deleteIfExists(directory.resolve(PASS_FILE));
            Files.deleteIfExists(directory.resolve(FAIL_FILE));
        } catch (IOException e) {
            System.err.println("Warning: Could not clean up old result files: " + e.getMessage());
        }
    }

    /**
     * 채점 결과를 기반으로 파일 내용을 생성
     * @param result 채점 결과
     * @return 파일 내용
     */
    private String generateFileContent(GradeResult result) {
        StringBuilder content = new StringBuilder();

        // 헤더
        content.append("=====================================\n");
        content.append("Week 1 Creational Patterns Grading Result\n");
        content.append("=====================================\n");
        content.append("Generated: ").append(LocalDateTime.now().format(DATE_FORMAT)).append("\n");
        content.append("Status: ").append(result.isPassed() ? "PASS" : "FAIL").append("\n");
        content.append("Score: ").append(String.format("%.1f", result.getScore())).append("%\n");
        content.append("Tests: ").append(result.getPassedTests()).append("/").append(result.getTotalTests()).append(" passed\n");
        content.append("\n");

        // 요약
        if (result.isPassed()) {
            content.append("🎉 CONGRATULATIONS! 🎉\n");
            content.append("Your implementation successfully demonstrates proper use of:\n");
            content.append("• Factory Pattern\n");
            content.append("• Singleton Pattern\n");
            content.append("• Object-Oriented Design Principles\n");
            content.append("\n");
        } else {
            content.append("❌ IMPROVEMENTS NEEDED\n");
            content.append("Your implementation needs attention in the following areas:\n");

            List<String> failures = result.getFailureMessages();
            for (int i = 0; i < Math.min(failures.size(), 5); i++) {
                content.append("• ").append(failures.get(i)).append("\n");
            }

            if (failures.size() > 5) {
                content.append("• ... and ").append(failures.size() - 5).append(" more issues (see details below)\n");
            }
            content.append("\n");
        }

        // 성공한 테스트들
        if (!result.getSuccessMessages().isEmpty()) {
            content.append("✅ SUCCESSFUL IMPLEMENTATIONS:\n");
            content.append("-------------------------------------\n");
            for (String success : result.getSuccessMessages()) {
                content.append("✓ ").append(success).append("\n");
            }
            content.append("\n");
        }

        // 실패한 테스트들
        if (!result.getFailureMessages().isEmpty()) {
            content.append("❌ ISSUES TO ADDRESS:\n");
            content.append("-------------------------------------\n");
            for (String failure : result.getFailureMessages()) {
                content.append("✗ ").append(failure).append("\n");
            }
            content.append("\n");
        }

        // 상세 로그
        content.append("DETAILED GRADING LOG:\n");
        content.append("-------------------------------------\n");
        for (String detail : result.getDetails()) {
            content.append(detail).append("\n");
        }
        content.append("\n");

        // 개선 제안 (실패한 경우)
        if (!result.isPassed()) {
            content.append("💡 IMPROVEMENT SUGGESTIONS:\n");
            content.append("-------------------------------------\n");
            content.append(generateImprovementSuggestions(result));
            content.append("\n");
        }

        // 학습 리소스
        content.append("📚 LEARNING RESOURCES:\n");
        content.append("-------------------------------------\n");
        content.append("• Factory Pattern: https://refactoring.guru/design-patterns/factory-method\n");
        content.append("• Singleton Pattern: https://refactoring.guru/design-patterns/singleton\n");
        content.append("• SOLID Principles: https://en.wikipedia.org/wiki/SOLID\n");
        content.append("• Java Design Patterns: https://java-design-patterns.com/\n");
        content.append("\n");

        // 푸터
        content.append("=====================================\n");
        content.append("End of Grading Report\n");
        content.append("=====================================\n");

        return content.toString();
    }

    /**
     * 실패한 테스트를 기반으로 개선 제안을 생성
     * @param result 채점 결과
     * @return 개선 제안 텍스트
     */
    private String generateImprovementSuggestions(GradeResult result) {
        StringBuilder suggestions = new StringBuilder();
        List<String> failures = result.getFailureMessages();

        // 실패 메시지를 분석해서 맞춤형 제안 생성
        for (String failure : failures) {
            String lower = failure.toLowerCase();

            if (lower.contains("processor interface") || lower.contains("interface")) {
                suggestions.append("• Create a Processor interface with common methods (e.g., process(), getType())\n");
            }
            if (lower.contains("factory") && lower.contains("method")) {
                suggestions.append("• Implement a factory method that creates processors based on type parameters\n");
            }
            if (lower.contains("private constructor")) {
                suggestions.append("• Make NodeManager constructor private to prevent external instantiation\n");
            }
            if (lower.contains("getinstance")) {
                suggestions.append("• Add a static getInstance() method that returns the singleton instance\n");
            }
            if (lower.contains("thread") && lower.contains("safe")) {
                suggestions.append("• Implement thread-safe singleton using double-checked locking pattern\n");
            }
            if (lower.contains("implementation") && lower.contains("3")) {
                suggestions.append("• Create at least 3 concrete Processor implementations (Data, Compute, IO)\n");
            }
            if (lower.contains("business logic")) {
                suggestions.append("• Separate singleton management logic from business operations\n");
            }
            if (lower.contains("unknown type")) {
                suggestions.append("• Add proper error handling for unsupported processor types\n");
            }
        }

        if (suggestions.length() == 0) {
            suggestions.append("• Review the Week1_CreationalPatterns_Bad.java file to understand the problems\n");
            suggestions.append("• Study the design patterns documentation\n");
            suggestions.append("• Ensure your implementation follows SOLID principles\n");
        }

        return suggestions.toString();
    }

    /**
     * 콘솔에 간단한 결과 요약을 출력
     * @param result 채점 결과
     */
    public void printSummary(GradeResult result) {
        System.out.println("\n" + "=".repeat(50));
        System.out.println("GRADING SUMMARY");
        System.out.println("=".repeat(50));
        System.out.println("Status: " + (result.isPassed() ? "✅ PASS" : "❌ FAIL"));
        System.out.println("Score: " + String.format("%.1f%%", result.getScore()));
        System.out.println("Tests: " + result.getPassedTests() + "/" + result.getTotalTests() + " passed");

        if (!result.isPassed()) {
            System.out.println("\nKey Issues:");
            List<String> failures = result.getFailureMessages();
            for (int i = 0; i < Math.min(failures.size(), 3); i++) {
                System.out.println("• " + failures.get(i));
            }
            if (failures.size() > 3) {
                System.out.println("• ... and " + (failures.size() - 3) + " more issues");
            }
        }

        System.out.println("=".repeat(50));
    }
}