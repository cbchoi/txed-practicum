package com.orca.patterns.grading;

import java.lang.reflect.*;
import java.util.*;

/**
 * Factory와 Singleton 패턴의 통합 동작을 검증하는 데코레이터
 */
public class IntegrationGrader extends GraderDecorator {

    private static final String PROCESSOR_INTERFACE = "Processor";
    private static final String FACTORY_CLASS = "ProcessorFactory";
    private static final String NODE_MANAGER_CLASS = "NodeManager";

    public IntegrationGrader(Grader grader) {
        super(grader);
    }

    @Override
    protected GradeResult performAdditionalGrading(String studentPackage) {
        GradeResult result = new GradeResult();
        result.addDetail("Starting Integration Testing");

        try {
            // 1. Factory와 Singleton이 함께 동작하는지 확인
            checkFactorySingletonIntegration(studentPackage, result);

            // 2. 확장성 테스트
            checkExtensibility(studentPackage, result);

            // 3. 실제 사용 시나리오 테스트
            checkRealWorldUsageScenario(studentPackage, result);

        } catch (Exception e) {
            result.addTest(false, "Integration testing failed with exception: " + e.getMessage());
        }

        return result;
    }

    private void checkFactorySingletonIntegration(String studentPackage, GradeResult result) {
        try {
            // NodeManager 인스턴스 획득
            Class<?> nodeManagerClass = Class.forName(studentPackage + "." + NODE_MANAGER_CLASS);
            Method getInstance = findGetInstanceMethod(nodeManagerClass);

            if (getInstance == null) {
                result.addTest(false, "Cannot find getInstance method for integration test");
                return;
            }

            Object nodeManager = getInstance.invoke(null);

            // Factory를 통한 processor 생성
            Class<?> factoryClass = Class.forName(studentPackage + "." + FACTORY_CLASS);
            Object factory = createFactoryInstance(factoryClass);

            if (factory == null) {
                result.addTest(false, "Cannot create factory instance for integration test");
                return;
            }

            Object processor = invokeFactoryMethod(factory, "DATA");

            if (nodeManager != null && processor != null) {
                result.addTest(true, "Factory and Singleton patterns work together successfully");
                result.addDetail("Successfully integrated NodeManager singleton with ProcessorFactory");
            } else {
                result.addTest(false, "Integration test failed - could not create both NodeManager and Processor instances");
            }

        } catch (Exception e) {
            result.addTest(false, "Factory-Singleton integration test failed: " + e.getMessage());
        }
    }

    private void checkExtensibility(String studentPackage, GradeResult result) {
        try {
            Class<?> processorInterface = Class.forName(studentPackage + "." + PROCESSOR_INTERFACE);
            List<Class<?>> implementations = findImplementations(studentPackage, processorInterface);

            if (implementations.size() >= 3) {
                result.addTest(true, "System shows good extensibility with " + implementations.size() + " processor implementations");

                // 각 구현체가 서로 다른 클래스인지 확인
                Set<String> classNames = new HashSet<>();
                for (Class<?> impl : implementations) {
                    classNames.add(impl.getSimpleName());
                }

                if (classNames.size() == implementations.size()) {
                    result.addTest(true, "All processor implementations are distinct classes");
                } else {
                    result.addTest(false, "Some processor implementations have duplicate names");
                }

            } else {
                result.addTest(false, "System needs better extensibility - should have at least 3 processor types");
            }

        } catch (Exception e) {
            result.addTest(false, "Extensibility test failed: " + e.getMessage());
        }
    }

    private void checkRealWorldUsageScenario(String studentPackage, GradeResult result) {
        try {
            // 실제 사용 시나리오: 여러 타입의 작업을 처리
            Class<?> nodeManagerClass = Class.forName(studentPackage + "." + NODE_MANAGER_CLASS);
            Class<?> factoryClass = Class.forName(studentPackage + "." + FACTORY_CLASS);
            Class<?> processorInterface = Class.forName(studentPackage + "." + PROCESSOR_INTERFACE);

            Method getInstance = findGetInstanceMethod(nodeManagerClass);
            Object nodeManager = getInstance.invoke(null);
            Object factory = createFactoryInstance(factoryClass);

            String[] taskTypes = {"DATA", "COMPUTE", "IO"};
            String[] testData = {"test data", "performance metrics", "log files"};

            int successfulTasks = 0;
            List<String> taskResults = new ArrayList<>();

            for (int i = 0; i < taskTypes.length; i++) {
                try {
                    Object processor = invokeFactoryMethod(factory, taskTypes[i]);
                    if (processor != null && processorInterface.isInstance(processor)) {

                        // process 메소드 호출 시도
                        Method processMethod = findProcessMethod(processor.getClass());
                        if (processMethod != null) {
                            Object result_obj = processMethod.invoke(processor, testData[i]);
                            if (result_obj != null) {
                                successfulTasks++;
                                taskResults.add(taskTypes[i] + " -> " + result_obj.toString());
                            }
                        }
                    }
                } catch (Exception e) {
                    // 개별 작업 실패는 기록하지만 전체 테스트는 계속
                    result.addDetail("Task " + taskTypes[i] + " failed: " + e.getMessage());
                }
            }

            if (successfulTasks >= 2) {
                result.addTest(true, "Real-world usage scenario successful (" + successfulTasks + "/" + taskTypes.length + " tasks completed)");
                result.addDetail("Task results: " + String.join(", ", taskResults));
            } else {
                result.addTest(false, "Real-world usage scenario failed - only " + successfulTasks + " tasks completed successfully");
            }

        } catch (Exception e) {
            result.addTest(false, "Real-world usage scenario test failed: " + e.getMessage());
        }
    }

    // Helper methods
    private Method findGetInstanceMethod(Class<?> nodeManagerClass) {
        for (Method method : nodeManagerClass.getMethods()) {
            if (method.getName().toLowerCase().contains("instance")
                    && Modifier.isStatic(method.getModifiers())
                    && method.getReturnType().equals(nodeManagerClass)
                    && method.getParameterCount() == 0) {
                return method;
            }
        }
        return null;
    }

    private Object createFactoryInstance(Class<?> factoryClass) {
        try {
            return factoryClass.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            return null;
        }
    }

    private Object invokeFactoryMethod(Object factory, String type) {
        try {
            Method[] methods = factory.getClass().getMethods();
            for (Method method : methods) {
                if (method.getParameterCount() == 1
                        && method.getParameterTypes()[0].equals(String.class)
                        && (method.getReturnType().getSimpleName().contains("Processor")
                        || method.getName().toLowerCase().contains("create"))) {
                    return method.invoke(factory, type);
                }
            }
        } catch (Exception e) {
            // Method invocation failed
        }
        return null;
    }

    private Method findProcessMethod(Class<?> processorClass) {
        try {
            // 가장 일반적인 메소드명들 시도
            String[] methodNames = {"process", "processData", "compute", "performIO"};
            for (String methodName : methodNames) {
                try {
                    return processorClass.getMethod(methodName, String.class);
                } catch (NoSuchMethodException e) {
                    // 다음 메소드명 시도
                }
            }

            // 모든 public 메소드 중에서 String을 받고 String을 반환하는 메소드 찾기
            for (Method method : processorClass.getMethods()) {
                if (method.getParameterCount() == 1
                        && method.getParameterTypes()[0].equals(String.class)
                        && method.getReturnType().equals(String.class)
                        && !method.getName().equals("toString")) {
                    return method;
                }
            }
        } catch (Exception e) {
            // Method search failed
        }
        return null;
    }

    private List<Class<?>> findImplementations(String studentPackage, Class<?> interfaceClass) {
        List<Class<?>> implementations = new ArrayList<>();
        String[] possibleNames = {
                "DataProcessor", "ComputeProcessor", "IOProcessor",
                "BadDataProcessor", "BadComputeProcessor", "BadIOProcessor",
                "DataProcessingStrategy", "ComputeProcessingStrategy", "IOProcessingStrategy"
        };

        for (String name : possibleNames) {
            try {
                Class<?> clazz = Class.forName(studentPackage + "." + name);
                if (interfaceClass.isAssignableFrom(clazz) && !clazz.isInterface()) {
                    implementations.add(clazz);
                }
            } catch (ClassNotFoundException e) {
                // 클래스가 없는 경우는 무시
            }
        }

        return implementations;
    }

    @Override
    protected String getAdditionalCategory() {
        return "Integration Tests";
    }
}