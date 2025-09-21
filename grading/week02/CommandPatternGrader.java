package com.orca.patterns.grading;

import java.lang.reflect.Method;
import java.lang.reflect.Constructor;

/**
 * Command Pattern 구현을 검증하는 채점기
 * Decorator 패턴의 ConcreteDecorator 역할
 */
public class CommandPatternGrader extends GraderDecorator {

    public CommandPatternGrader(Grader grader) {
        super(grader);
    }

    @Override
    public GradeResult grade(String studentPackage) {
        GradeResult previousResult = wrappedGrader.grade(studentPackage);
        GradeResult result = new GradeResult();

        result.addDetail("=== Command Pattern Grading ===");

        try {
            // 1. Command 인터페이스 검증
            gradeCommandInterface(studentPackage, result);

            // 2. ProcessCommand 클래스 검증
            gradeProcessCommandClass(studentPackage, result);

            // 3. CommandInvoker 클래스 검증
            gradeCommandInvokerClass(studentPackage, result);

            // 4. 통합 테스트
            gradeCommandIntegration(studentPackage, result);

        } catch (Exception e) {
            result.addTest(false, "Command Pattern grading failed: " + e.getMessage());
            result.addDetail("Exception: " + e.getClass().getSimpleName());
        }

        return mergeResults(previousResult, result);
    }

    private void gradeCommandInterface(String studentPackage, GradeResult result) {
        try {
            Class<?> commandInterface = Class.forName(studentPackage + ".Command");

            if (!commandInterface.isInterface()) {
                result.addTest(false, "Command must be an interface");
                return;
            }

            Method[] methods = commandInterface.getDeclaredMethods();
            boolean hasExecute = false;
            boolean hasUndo = false;
            boolean hasGetDescription = false;
            boolean hasGetCommandId = false;

            for (Method method : methods) {
                String methodName = method.getName();
                if ("execute".equals(methodName) && method.getParameterCount() == 0) {
                    hasExecute = true;
                }
                if ("undo".equals(methodName) && method.getParameterCount() == 0) {
                    hasUndo = true;
                }
                if ("getDescription".equals(methodName) && method.getParameterCount() == 0) {
                    hasGetDescription = true;
                }
                if ("getCommandId".equals(methodName) && method.getParameterCount() == 0) {
                    hasGetCommandId = true;
                }
            }

            if (hasExecute && hasUndo && hasGetDescription && hasGetCommandId) {
                result.addTest(true, "Command interface is properly defined");
                result.addDetail("Found required methods: execute(), undo(), getDescription(), getCommandId()");
            } else {
                result.addTest(false, "Command interface missing required methods");
                result.addDetail("Required: execute(), undo(), getDescription(), getCommandId()");
                if (!hasExecute) result.addDetail("Missing: execute() method");
                if (!hasUndo) result.addDetail("Missing: undo() method");
                if (!hasGetDescription) result.addDetail("Missing: getDescription() method");
                if (!hasGetCommandId) result.addDetail("Missing: getCommandId() method");
            }

        } catch (ClassNotFoundException e) {
            result.addTest(false, "Command interface not found");
            result.addDetail("Make sure Command interface exists in the package");
        }
    }

    private void gradeProcessCommandClass(String studentPackage, GradeResult result) {
        try {
            Class<?> processCommandClass = Class.forName(studentPackage + ".ProcessCommand");
            Class<?> commandInterface = Class.forName(studentPackage + ".Command");

            if (processCommandClass.isInterface()) {
                result.addTest(false, "ProcessCommand must be a class, not an interface");
                return;
            }

            // Command 인터페이스 구현 확인
            if (commandInterface.isAssignableFrom(processCommandClass)) {
                result.addTest(true, "ProcessCommand implements Command interface");
            } else {
                result.addTest(false, "ProcessCommand does not implement Command interface");
            }

            // 생성자 확인
            Constructor<?>[] constructors = processCommandClass.getDeclaredConstructors();
            boolean hasParameterizedConstructor = false;

            for (Constructor<?> constructor : constructors) {
                if (constructor.getParameterCount() > 0) {
                    hasParameterizedConstructor = true;
                    break;
                }
            }

            if (hasParameterizedConstructor) {
                result.addTest(true, "ProcessCommand has parameterized constructor");
                result.addDetail("ProcessCommand can be initialized with parameters");
            } else {
                result.addTest(false, "ProcessCommand missing parameterized constructor");
                result.addDetail("ProcessCommand should accept parameters in constructor");
            }

        } catch (ClassNotFoundException e) {
            result.addTest(false, "ProcessCommand class not found");
            result.addDetail("Make sure ProcessCommand class exists in the package");
        }
    }

    private void gradeCommandInvokerClass(String studentPackage, GradeResult result) {
        try {
            Class<?> invokerClass = Class.forName(studentPackage + ".CommandInvoker");

            Method[] methods = invokerClass.getDeclaredMethods();
            boolean hasExecuteCommand = false;
            boolean hasUndoCommand = false;
            boolean hasHistory = false;

            for (Method method : methods) {
                String methodName = method.getName().toLowerCase();
                if (methodName.contains("execute") && method.getParameterCount() >= 1) {
                    hasExecuteCommand = true;
                }
                if (methodName.contains("undo")) {
                    hasUndoCommand = true;
                }
                if (methodName.contains("history") || methodName.contains("get")) {
                    hasHistory = true;
                }
            }

            if (hasExecuteCommand) {
                result.addTest(true, "CommandInvoker has execute method");
            } else {
                result.addTest(false, "CommandInvoker missing execute method");
            }

            if (hasUndoCommand) {
                result.addTest(true, "CommandInvoker has undo functionality");
            } else {
                result.addTest(false, "CommandInvoker missing undo functionality");
            }

            if (hasHistory) {
                result.addTest(true, "CommandInvoker has history management");
            } else {
                result.addTest(false, "CommandInvoker missing history management");
            }

            result.addDetail("CommandInvoker should manage command execution, undo, and history");

        } catch (ClassNotFoundException e) {
            result.addTest(false, "CommandInvoker class not found");
            result.addDetail("Make sure CommandInvoker class exists in the package");
        }
    }

    private void gradeCommandIntegration(String studentPackage, GradeResult result) {
        try {
            // CommandInvoker 인스턴스 생성
            Class<?> invokerClass = Class.forName(studentPackage + ".CommandInvoker");
            Object invoker = invokerClass.getDeclaredConstructor().newInstance();

            // ProcessCommand 클래스 확인
            Class<?> processCommandClass = Class.forName(studentPackage + ".ProcessCommand");

            // 기본적인 인스턴스 생성이 가능한지 확인
            try {
                Constructor<?>[] constructors = processCommandClass.getDeclaredConstructors();
                Object command = null;

                // 매개변수가 있는 생성자 시도
                for (Constructor<?> constructor : constructors) {
                    if (constructor.getParameterCount() > 0) {
                        // 간단한 매개변수로 시도
                        Class<?>[] paramTypes = constructor.getParameterTypes();
                        Object[] params = new Object[paramTypes.length];

                        for (int i = 0; i < paramTypes.length; i++) {
                            if (paramTypes[i] == String.class) {
                                params[i] = "test";
                            } else if (paramTypes[i].isPrimitive()) {
                                if (paramTypes[i] == int.class) params[i] = 0;
                                else if (paramTypes[i] == boolean.class) params[i] = false;
                                else if (paramTypes[i] == long.class) params[i] = 0L;
                                else if (paramTypes[i] == double.class) params[i] = 0.0;
                            } else {
                                params[i] = null;
                            }
                        }

                        try {
                            command = constructor.newInstance(params);
                            break;
                        } catch (Exception e) {
                            // 다른 생성자 시도
                            continue;
                        }
                    }
                }

                if (command != null) {
                    result.addTest(true, "Command pattern integration test passed");
                    result.addDetail("Successfully created CommandInvoker and ProcessCommand instances");
                } else {
                    result.addTest(false, "Failed to create ProcessCommand instance");
                    result.addDetail("ProcessCommand constructor may require specific parameters");
                }

            } catch (Exception e) {
                result.addTest(false, "Command integration test failed: " + e.getMessage());
                result.addDetail("Error creating command instances");
            }

        } catch (Exception e) {
            result.addTest(false, "Command integration test failed: " + e.getMessage());
            result.addDetail("Error creating invoker instance");
        }
    }

    @Override
    public String getGradingCategory() {
        return wrappedGrader.getGradingCategory() + " + Command Pattern";
    }
}