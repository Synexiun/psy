import { ESLintUtils } from '@typescript-eslint/utils';
import { isClinicalNumericIdentifier } from '../clinical-numbers.js';
const createRule = ESLintUtils.RuleCreator((name) => `https://docs.disciplineos.internal/eslint/${name}`);
const BOOLEAN_SUFFIXES = [
    'Skipped',
    'Completed',
    'Enabled',
    'Pending',
    'Required',
    'Visible',
    'Active',
    'Disabled',
];
function hasBooleanSuffix(name) {
    return BOOLEAN_SUFFIXES.some((suffix) => name.endsWith(suffix));
}
function isClinicalAndNumeric(name) {
    return isClinicalNumericIdentifier(name) && !hasBooleanSuffix(name);
}
function classNameHasClinicalToken(node) {
    for (const attr of node.attributes) {
        if (attr.type !== 'JSXAttribute' ||
            attr.name.type !== 'JSXIdentifier' ||
            attr.name.name !== 'className') {
            continue;
        }
        const value = attr.value;
        if (!value || value.type !== 'Literal' || typeof value.value !== 'string') {
            return true;
        }
        const tokens = value.value.split(/\s+/);
        return tokens.includes('clinical-number');
    }
    return false;
}
function isFormatNumberClinicalCall(node) {
    if (node.type !== 'CallExpression')
        return false;
    const { callee } = node;
    if (callee.type === 'Identifier' && callee.name === 'formatNumberClinical')
        return true;
    if (callee.type === 'MemberExpression' &&
        !callee.computed &&
        callee.property.type === 'Identifier' &&
        callee.property.name === 'formatNumberClinical')
        return true;
    return false;
}
export const rule = createRule({
    name: 'clinical-numbers-must-format',
    meta: {
        type: 'problem',
        docs: {
            description: 'Clinical numeric values must be wrapped in formatNumberClinical() or rendered inside an element with className containing "clinical-number"',
        },
        messages: {
            wrapClinicalNumber: "Clinical numeric value '{{name}}' must be wrapped in formatNumberClinical() or rendered inside an element with className containing 'clinical-number'",
        },
        schema: [],
    },
    defaultOptions: [],
    create(context) {
        function enclosingJSXElementHasClinicalToken(node) {
            let current = node.parent;
            while (current !== undefined) {
                if (current.type === 'JSXElement') {
                    if (classNameHasClinicalToken(current.openingElement))
                        return true;
                }
                if (current.type === 'FunctionDeclaration' ||
                    current.type === 'FunctionExpression' ||
                    current.type === 'ArrowFunctionExpression' ||
                    current.type === 'Program') {
                    return false;
                }
                current = current.parent;
            }
            return false;
        }
        return {
            JSXExpressionContainer(node) {
                const expression = node.expression;
                // Skip empty expressions and spread children
                if (expression.type === 'JSXEmptyExpression') {
                    return;
                }
                // Check ancestor JSX elements for className escape hatch
                if (enclosingJSXElementHasClinicalToken(node)) {
                    return;
                }
                // Check for formatNumberClinical(...) call escape hatch
                if (isFormatNumberClinicalCall(expression)) {
                    return;
                }
                // Case 1: bare identifier — {identifier}
                if (expression.type === 'Identifier') {
                    const name = expression.name;
                    if (isClinicalAndNumeric(name)) {
                        context.report({
                            node,
                            messageId: 'wrapClinicalNumber',
                            data: { name },
                        });
                    }
                    return;
                }
                // Case 2: member expression — {object.property}
                if (expression.type === 'MemberExpression') {
                    const property = expression.property;
                    // Only handle static (non-computed) member access: obj.prop
                    if (!expression.computed && property.type === 'Identifier') {
                        const name = property.name;
                        if (isClinicalAndNumeric(name)) {
                            context.report({
                                node,
                                messageId: 'wrapClinicalNumber',
                                data: { name },
                            });
                        }
                    }
                }
            },
        };
    },
});
//# sourceMappingURL=clinical-numbers-must-format.js.map