package com.orca.patterns.grading;

import java.lang.reflect.*;
import java.util.*;

/**
 * Factory Pattern 구현을 검증하는 데코레이터
 */
public class FactoryPatternGrader extends GraderDecorator {

    private static final String PROCESSOR_INTERFACE = "Processor";
    private static final String FACTORY_CLASS = "ProcessorFactory";

    public FactoryPatternGrader(Grader grader) {
        super(grader);
    }

    @Override
    protected GradeResult performAdditionalGrading(String studentPackage) {
        GradeResult result = new GradeResult();
        result.addDetail("Starting Factory Pattern validation");

        try {
            // 1. Processor 인터페이스 존재 확인
            checkProcessorInterface(studentPackage, result);

            // 2. ProcessorFactory 클래스 존재 확인
            checkProcessorFactory(studentPackage, result);

            // 3. 최소 3개의 구현체 존재 확인
            checkProcessorImplementations(studentPackage, result);

            // 4. Factory를 통한 객체 생성 확인
            checkFactoryObjectCreation(studentPackage, result);

            // 5. 알 수 없는 타입 처리 확인
            checkUnknownTypeHandling(studentPackage, result);

        } catch (Exception e) {
            result.addTest(false, "Factory Pattern validation failed with exception: " + e.getMessage());
        }

        return result;
    }

    private void checkProcessorInterface(String studentPackage, GradeResult result) {
        try {
            Class<?> processorClass = Class.forName(studentPackage + "." + PROCESSOR_INTERFACE);

            if (!processorClass.isInterface()) {
                result.addTest(false, "Processor should be an interface, but found a class");
                return;
            }

            Method[] methods = processorClass.getDeclaredMethods();
            if (methods.length == 0) {
                result.addTest(false, "Processor interface should have at least one method");
                return;
            }

            result.addTest(true, "Processor interface exists and has methods");
            result.addDetail("Found " + methods.length + " methods in Processor interface");

        } catch (ClassNotFoundException e) {
            result.addTest(false, "Processor interface not found in package " + studentPackage);
        }
    }

    private void checkProcessorFactory(String studentPackage, GradeResult result) {
        try {
            Class<?> factoryClass = Class.forName(studentPackage + "." + FACTORY_CLASS);

            Method[] methods = factoryClass.getMethods();
            boolean hasFactoryMethod = Arrays.stream(methods)
                    .anyMatch(m -> m.getReturnType().getSimpleName().contains("Processor")
                            && m.getParameterCount() >= 1);

            if (!hasFactoryMethod) {
                result.addTest(false, "ProcessorFactory should have a factory method that returns Processor");
                return;
            }

            result.addTest(true, "ProcessorFactory class exists with appropriate factory method");

        } catch (ClassNotFoundException e) {
            result.addTest(false, "ProcessorFactory class not found in package " + studentPackage);
        }
    }

    private void checkProcessorImplementations(String studentPackage, GradeResult result) {
        try {
            Class<?> processorInterface = Class.forName(studentPackage + "." + PROCESSOR_INTERFACE);
            List<Class<?>> implementations = findImplementations(studentPackage, processorInterface);

            if (implementations.size() < 3) {
                result.addTest(false, "Should have at least 3 Processor implementations. Found: " + implementations.size());
                return;
            }

            // 각 구현체가 인스턴스화 가능한지 확인
            for (Class<?> impl : implementations) {
                try {
                    Constructor<?> constructor = impl.getDeclaredConstructor();
                    constructor.setAccessible(true);
                    Object instance = constructor.newInstance();

                    if (!processorInterface.isInstance(instance)) {
                        result.addTest(false, impl.getSimpleName() + " does not properly implement Processor interface");
                        return;
                    }
                } catch (Exception e) {
                    result.addTest(false, "Cannot instantiate " + impl.getSimpleName() + ": " + e.getMessage());
                    return;
                }
            }

            result.addTest(true, "Found " + implementations.size() + " valid Processor implementations");
            result.addDetail("Implementations: " + implementations.stream()
                    .map(Class::getSimpleName)
                    .reduce((a, b) -> a + ", " + b).orElse("none"));

        } catch (ClassNotFoundException e) {
            result.addTest(false, "Cannot find Processor interface for implementation check");
        }
    }

    private void checkFactoryObjectCreation(String studentPackage, GradeResult result) {
        try {
            Class<?> factoryClass = Class.forName(studentPackage + "." + FACTORY_CLASS);
            Class<?> processorInterface = Class.forName(studentPackage + "." + PROCESSOR_INTERFACE);

            Object factory = createFactoryInstance(factoryClass);
            if (factory == null) {
                result.addTest(false, "Cannot create factory instance");
                return;
            }

            String[] testTypes = {"DATA", "COMPUTE", "IO", "data", "compute", "io"};
            int successCount = 0;

            for (String type : testTypes) {
                Object processor = invokeFactoryMethod(factory, type);
                if (processor != null && processorInterface.isInstance(processor)) {
                    successCount++;
                }
            }

            if (successCount < 2) {
                result.addTest(false, "Factory should be able to create at least 2 different types of processors");
                return;
            }

            result.addTest(true, "Factory successfully creates multiple processor types");
            result.addDetail("Successfully created processors for " + successCount + " different types");

        } catch (Exception e) {
            result.addTest(false, "Factory object creation test failed: " + e.getMessage());
        }
    }

    private void checkUnknownTypeHandling(String studentPackage, GradeResult result) {
        try {
            Class<?> factoryClass = Class.forName(studentPackage + "." + FACTORY_CLASS);
            Object factory = createFactoryInstance(factoryClass);

            if (factory == null) {
                result.addTest(false, "Cannot create factory instance for unknown type test");
                return;
            }

            try {
                Object unknownResult = invokeFactoryMethod(factory, "UNKNOWN_TYPE");
                // null 반환이나 예외 발생 모두 허용
                result.addTest(true, "Factory handles unknown types gracefully");
            } catch (Exception e) {
                // 예외 발생도 적절한 처리로 간주
                result.addTest(true, "Factory handles unknown types by throwing exception");
            }

        } catch (Exception e) {
            result.addTest(false, "Unknown type handling test failed: " + e.getMessage());
        }
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

    private Object createFactoryInstance(Class<?> factoryClass) {
        try {
            return factoryClass.getDeclaredConstructor().newInstance();
        } catch (NoSuchMethodException e) {
            // 정적 팩토리 메소드 찾기
            Method[] methods = factoryClass.getMethods();
            for (Method method : methods) {
                if (Modifier.isStatic(method.getModifiers())
                        && method.getReturnType().equals(factoryClass)
                        && method.getParameterCount() == 0) {
                    try {
                        return method.invoke(null);
                    } catch (Exception ex) {
                        return null;
                    }
                }
            }
            return null;
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
            return null;
        } catch (Exception e) {
            throw new RuntimeException("Factory method invocation failed", e);
        }
    }

    @Override
    protected String getAdditionalCategory() {
        return "Factory Pattern";
    }
}