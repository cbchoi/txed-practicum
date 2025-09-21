package com.orca.patterns.grading;

import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.*;

/**
 * Singleton Pattern 구현을 검증하는 데코레이터
 */
public class SingletonPatternGrader extends GraderDecorator {

    private static final String NODE_MANAGER_CLASS = "NodeManager";

    public SingletonPatternGrader(Grader grader) {
        super(grader);
    }

    @Override
    protected GradeResult performAdditionalGrading(String studentPackage) {
        GradeResult result = new GradeResult();
        result.addDetail("Starting Singleton Pattern validation");

        try {
            // 1. NodeManager 클래스 존재 확인
            Class<?> nodeManagerClass = checkNodeManagerExists(studentPackage, result);
            if (nodeManagerClass == null) {
                return result;
            }

            // 2. Private 생성자 확인
            checkPrivateConstructor(nodeManagerClass, result);

            // 3. getInstance 메소드 확인
            Method getInstanceMethod = checkGetInstanceMethod(nodeManagerClass, result);
            if (getInstanceMethod == null) {
                return result;
            }

            // 4. Singleton 동작 확인
            checkSingletonBehavior(getInstanceMethod, result);

            // 5. Thread Safety 확인
            checkThreadSafety(getInstanceMethod, result);

            // 6. 비즈니스 로직 분리 확인
            checkBusinessLogicSeparation(nodeManagerClass, result);

        } catch (Exception e) {
            result.addTest(false, "Singleton Pattern validation failed with exception: " + e.getMessage());
        }

        return result;
    }

    private Class<?> checkNodeManagerExists(String studentPackage, GradeResult result) {
        try {
            Class<?> nodeManagerClass = Class.forName(studentPackage + "." + NODE_MANAGER_CLASS);
            result.addTest(true, "NodeManager class exists");
            return nodeManagerClass;
        } catch (ClassNotFoundException e) {
            result.addTest(false, "NodeManager class not found in package " + studentPackage);
            return null;
        }
    }

    private void checkPrivateConstructor(Class<?> nodeManagerClass, GradeResult result) {
        Constructor<?>[] constructors = nodeManagerClass.getDeclaredConstructors();
        boolean hasPrivateConstructor = Arrays.stream(constructors)
                .anyMatch(c -> Modifier.isPrivate(c.getModifiers()));

        if (hasPrivateConstructor) {
            result.addTest(true, "NodeManager has private constructor");
        } else {
            result.addTest(false, "NodeManager should have a private constructor to prevent external instantiation");
        }
    }

    private Method checkGetInstanceMethod(Class<?> nodeManagerClass, GradeResult result) {
        Method getInstance = null;
        for (Method method : nodeManagerClass.getMethods()) {
            if (method.getName().toLowerCase().contains("instance")
                    && Modifier.isStatic(method.getModifiers())
                    && method.getReturnType().equals(nodeManagerClass)
                    && method.getParameterCount() == 0) {
                getInstance = method;
                break;
            }
        }

        if (getInstance != null) {
            result.addTest(true, "NodeManager has static getInstance() method");
            return getInstance;
        } else {
            result.addTest(false, "NodeManager should have a static getInstance() method that returns NodeManager instance");
            return null;
        }
    }

    private void checkSingletonBehavior(Method getInstance, GradeResult result) {
        try {
            Object instance1 = getInstance.invoke(null);
            Object instance2 = getInstance.invoke(null);

            if (instance1 == instance2) {
                result.addTest(true, "getInstance() returns the same instance (singleton behavior verified)");
            } else {
                result.addTest(false, "getInstance() should always return the same instance");
            }
        } catch (Exception e) {
            result.addTest(false, "Failed to test singleton behavior: " + e.getMessage());
        }
    }

    private void checkThreadSafety(Method getInstance, GradeResult result) {
        try {
            final int THREAD_COUNT = 50;
            Set<Object> instances = ConcurrentHashMap.newKeySet();
            CountDownLatch latch = new CountDownLatch(THREAD_COUNT);
            List<Exception> exceptions = Collections.synchronizedList(new ArrayList<>());

            for (int i = 0; i < THREAD_COUNT; i++) {
                new Thread(() -> {
                    try {
                        Object instance = getInstance.invoke(null);
                        instances.add(instance);
                    } catch (Exception e) {
                        exceptions.add(e);
                    } finally {
                        latch.countDown();
                    }
                }).start();
            }

            boolean finished = latch.await(10, TimeUnit.SECONDS);

            if (!finished) {
                result.addTest(false, "Thread safety test timed out");
                return;
            }

            if (!exceptions.isEmpty()) {
                result.addTest(false, "Thread safety test failed with exceptions: " + exceptions.get(0).getMessage());
                return;
            }

            if (instances.size() == 1) {
                result.addTest(true, "Singleton is thread-safe (only one instance created across " + THREAD_COUNT + " threads)");
            } else {
                result.addTest(false, "Singleton is not thread-safe. " + instances.size() + " different instances were created");
            }

        } catch (Exception e) {
            result.addTest(false, "Thread safety test failed: " + e.getMessage());
        }
    }

    private void checkBusinessLogicSeparation(Class<?> nodeManagerClass, GradeResult result) {
        try {
            Method[] methods = nodeManagerClass.getMethods();
            boolean hasBusinessMethods = Arrays.stream(methods)
                    .anyMatch(m -> !m.getName().toLowerCase().contains("instance")
                            && !isObjectMethod(m.getName())
                            && !m.getName().equals("getClass"));

            if (hasBusinessMethods) {
                result.addTest(true, "NodeManager has business logic methods separated from singleton management");

                // 비즈니스 메소드 목록 출력
                List<String> businessMethods = Arrays.stream(methods)
                        .filter(m -> !m.getName().toLowerCase().contains("instance")
                                && !isObjectMethod(m.getName())
                                && !m.getName().equals("getClass"))
                        .map(Method::getName)
                        .collect(ArrayList::new, ArrayList::add, ArrayList::addAll);

                result.addDetail("Business methods found: " + String.join(", ", businessMethods));
            } else {
                result.addTest(false, "NodeManager should have business logic methods for node management");
            }

        } catch (Exception e) {
            result.addTest(false, "Business logic separation check failed: " + e.getMessage());
        }
    }

    private boolean isObjectMethod(String methodName) {
        return methodName.equals("hashCode") || methodName.equals("equals")
                || methodName.equals("toString") || methodName.equals("wait")
                || methodName.equals("notify") || methodName.equals("notifyAll");
    }

    @Override
    protected String getAdditionalCategory() {
        return "Singleton Pattern";
    }
}