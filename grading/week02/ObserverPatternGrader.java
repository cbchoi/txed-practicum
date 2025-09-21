package com.orca.patterns.grading;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.Arrays;
import java.util.List;

/**
 * Observer Pattern 구현을 검증하는 채점기
 * Decorator 패턴의 ConcreteDecorator 역할
 */
public class ObserverPatternGrader extends GraderDecorator {

    public ObserverPatternGrader(Grader grader) {
        super(grader);
    }

    @Override
    public GradeResult grade(String studentPackage) {
        GradeResult previousResult = wrappedGrader.grade(studentPackage);
        GradeResult result = new GradeResult();

        result.addDetail("=== Observer Pattern Grading ===");

        try {
            // 1. EventObserver 인터페이스 검증
            gradeEventObserverInterface(studentPackage, result);

            // 2. ProcessEvent 클래스 검증
            gradeProcessEventClass(studentPackage, result);

            // 3. EventPublisher 클래스 검증
            gradeEventPublisherClass(studentPackage, result);

            // 4. Observer 구현체들 검증
            gradeObserverImplementations(studentPackage, result);

            // 5. 통합 테스트
            gradeObserverIntegration(studentPackage, result);

        } catch (Exception e) {
            result.addTest(false, "Observer Pattern grading failed: " + e.getMessage());
            result.addDetail("Exception: " + e.getClass().getSimpleName());
        }

        return mergeResults(previousResult, result);
    }

    private void gradeEventObserverInterface(String studentPackage, GradeResult result) {
        try {
            Class<?> observerInterface = Class.forName(studentPackage + ".EventObserver");

            if (!observerInterface.isInterface()) {
                result.addTest(false, "EventObserver must be an interface");
                return;
            }

            Method[] methods = observerInterface.getDeclaredMethods();
            boolean hasOnEvent = false;
            boolean hasGetObserverId = false;

            for (Method method : methods) {
                if ("onEvent".equals(method.getName()) && method.getParameterCount() == 1) {
                    hasOnEvent = true;
                }
                if ("getObserverId".equals(method.getName()) && method.getParameterCount() == 0) {
                    hasGetObserverId = true;
                }
            }

            if (hasOnEvent && hasGetObserverId) {
                result.addTest(true, "EventObserver interface is properly defined");
                result.addDetail("Found required methods: onEvent() and getObserverId()");
            } else {
                result.addTest(false, "EventObserver interface missing required methods");
                result.addDetail("Required: onEvent(ProcessEvent), getObserverId()");
            }

        } catch (ClassNotFoundException e) {
            result.addTest(false, "EventObserver interface not found");
            result.addDetail("Make sure EventObserver interface exists in the package");
        }
    }

    private void gradeProcessEventClass(String studentPackage, GradeResult result) {
        try {
            Class<?> eventClass = Class.forName(studentPackage + ".ProcessEvent");

            if (eventClass.isInterface()) {
                result.addTest(false, "ProcessEvent must be a class, not an interface");
                return;
            }

            // 필요한 필드들이 있는지 확인 (getter 메소드로 확인)
            Method[] methods = eventClass.getDeclaredMethods();
            boolean hasGetId = false;
            boolean hasGetType = false;
            boolean hasGetMessage = false;
            boolean hasGetTimestamp = false;

            for (Method method : methods) {
                String methodName = method.getName();
                if (methodName.startsWith("get") && method.getParameterCount() == 0) {
                    if (methodName.contains("Id")) hasGetId = true;
                    if (methodName.contains("Type")) hasGetType = true;
                    if (methodName.contains("Message")) hasGetMessage = true;
                    if (methodName.contains("Time")) hasGetTimestamp = true;
                }
            }

            if (hasGetId && hasGetType && hasGetMessage && hasGetTimestamp) {
                result.addTest(true, "ProcessEvent class has required properties");
                result.addDetail("Found getter methods for: id, type, message, timestamp");
            } else {
                result.addTest(false, "ProcessEvent class missing required getter methods");
                result.addDetail("Required getters: getId(), getType(), getMessage(), getTimestamp()");
            }

        } catch (ClassNotFoundException e) {
            result.addTest(false, "ProcessEvent class not found");
            result.addDetail("Make sure ProcessEvent class exists in the package");
        }
    }

    private void gradeEventPublisherClass(String studentPackage, GradeResult result) {
        try {
            Class<?> publisherClass = Class.forName(studentPackage + ".EventPublisher");

            Method[] methods = publisherClass.getDeclaredMethods();
            boolean hasAddObserver = false;
            boolean hasRemoveObserver = false;
            boolean hasPublishEvent = false;

            for (Method method : methods) {
                String methodName = method.getName();
                if (methodName.contains("add") || methodName.contains("register") || methodName.contains("subscribe")) {
                    hasAddObserver = true;
                }
                if (methodName.contains("remove") || methodName.contains("unregister") || methodName.contains("unsubscribe")) {
                    hasRemoveObserver = true;
                }
                if (methodName.contains("publish") || methodName.contains("notify") || methodName.contains("fire")) {
                    hasPublishEvent = true;
                }
            }

            if (hasAddObserver && hasRemoveObserver && hasPublishEvent) {
                result.addTest(true, "EventPublisher class has required methods");
                result.addDetail("Found methods for: add/remove observers, publish events");
            } else {
                result.addTest(false, "EventPublisher class missing required methods");
                result.addDetail("Required methods: addObserver, removeObserver, publishEvent");
            }

        } catch (ClassNotFoundException e) {
            result.addTest(false, "EventPublisher class not found");
            result.addDetail("Make sure EventPublisher class exists in the package");
        }
    }

    private void gradeObserverImplementations(String studentPackage, GradeResult result) {
        try {
            // LoggingObserver 검증
            try {
                Class<?> loggingObserver = Class.forName(studentPackage + ".LoggingObserver");
                Class<?> observerInterface = Class.forName(studentPackage + ".EventObserver");

                if (observerInterface.isAssignableFrom(loggingObserver)) {
                    result.addTest(true, "LoggingObserver implements EventObserver");
                } else {
                    result.addTest(false, "LoggingObserver does not implement EventObserver");
                }
            } catch (ClassNotFoundException e) {
                result.addTest(false, "LoggingObserver class not found");
            }

            // AlertingObserver 검증
            try {
                Class<?> alertingObserver = Class.forName(studentPackage + ".AlertingObserver");
                Class<?> observerInterface = Class.forName(studentPackage + ".EventObserver");

                if (observerInterface.isAssignableFrom(alertingObserver)) {
                    result.addTest(true, "AlertingObserver implements EventObserver");
                } else {
                    result.addTest(false, "AlertingObserver does not implement EventObserver");
                }
            } catch (ClassNotFoundException e) {
                result.addTest(false, "AlertingObserver class not found");
            }

        } catch (Exception e) {
            result.addTest(false, "Error validating Observer implementations: " + e.getMessage());
        }
    }

    private void gradeObserverIntegration(String studentPackage, GradeResult result) {
        try {
            // EventPublisher 인스턴스 생성
            Class<?> publisherClass = Class.forName(studentPackage + ".EventPublisher");
            Object publisher = publisherClass.getDeclaredConstructor().newInstance();

            // ProcessEvent 인스턴스 생성
            Class<?> eventClass = Class.forName(studentPackage + ".ProcessEvent");
            Constructor<?> eventConstructor = eventClass.getDeclaredConstructors()[0];
            Object event = null;

            // 다양한 생성자 시도
            try {
                if (eventConstructor.getParameterCount() >= 4) {
                    event = eventConstructor.newInstance("test-id", "INFO", "Test message", System.currentTimeMillis());
                } else if (eventConstructor.getParameterCount() >= 3) {
                    event = eventConstructor.newInstance("test-id", "INFO", "Test message");
                } else if (eventConstructor.getParameterCount() >= 2) {
                    event = eventConstructor.newInstance("test-id", "Test message");
                }
            } catch (Exception e) {
                // 기본 생성자 시도
                event = eventClass.getDeclaredConstructor().newInstance();
            }

            if (event != null) {
                result.addTest(true, "Observer pattern integration test passed");
                result.addDetail("Successfully created EventPublisher and ProcessEvent instances");
            } else {
                result.addTest(false, "Failed to create ProcessEvent instance");
            }

        } catch (Exception e) {
            result.addTest(false, "Observer integration test failed: " + e.getMessage());
            result.addDetail("Error creating instances for integration test");
        }
    }

    @Override
    public String getGradingCategory() {
        return wrappedGrader.getGradingCategory() + " + Observer Pattern";
    }
}