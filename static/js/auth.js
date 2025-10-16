/**
 * 认证相关JavaScript
 * Authentication JavaScript
 */

// 全局变量
let isSubmitting = false;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeAuth();
});

/**
 * 初始化认证功能
 */
function initializeAuth() {
    // 根据当前页面初始化不同的功能
    if (document.getElementById('loginForm')) {
        initializeLogin();
    }
    if (document.getElementById('registerForm')) {
        initializeRegister();
    }
    
}

/**
 * 初始化登录功能
 */
function initializeLogin() {
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    
    loginForm.addEventListener('submit', handleLogin);
    
    // 实时验证
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    
    usernameInput.addEventListener('blur', validateUsername);
    passwordInput.addEventListener('blur', validatePassword);
}

/**
 * 初始化注册功能
 */
function initializeRegister() {
    const registerForm = document.getElementById('registerForm');
    const registerBtn = document.getElementById('registerBtn');
    
    registerForm.addEventListener('submit', handleRegister);
    
    // 实时验证
    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const verificationCodeInput = document.getElementById('verification_code');
    
    usernameInput.addEventListener('blur', validateUsername);
    usernameInput.addEventListener('input', debounce(checkUsernameAvailability, 500));
    
    emailInput.addEventListener('blur', validateEmail);
    emailInput.addEventListener('input', debounce(checkEmailAvailability, 500));
    emailInput.addEventListener('input', handleEmailChange);
    
    passwordInput.addEventListener('input', validatePasswordStrength);
    passwordInput.addEventListener('blur', validatePassword);
    
    confirmPasswordInput.addEventListener('blur', validateConfirmPassword);
    
    verificationCodeInput.addEventListener('blur', validateVerificationCode);
    
    // 验证码相关事件
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    const resendCodeLink = document.getElementById('resendCodeLink');
    
    sendCodeBtn.addEventListener('click', handleSendVerificationCode);
    resendCodeLink.addEventListener('click', handleResendVerificationCode);
}


/**
 * 处理登录表单提交
 */
async function handleLogin(event) {
    event.preventDefault();
    
    if (isSubmitting) return;
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // 验证表单
    if (!validateLoginForm(data)) {
        return;
    }
    
    setLoading(true);
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 保存token到localStorage
            if (result.token) {
                localStorage.setItem('auth_token', result.token);
            }
            
            // 处理"记住我"选项
            const rememberMe = data.remember_me === 'on';
            localStorage.setItem('remember_me', rememberMe.toString());
            
            showSuccess('登录成功！正在跳转...');
            
            // 延迟跳转到主页
            setTimeout(() => {
                window.location.href = '/';
            }, 1500);
        } else {
            showError(result.error || '登录失败');
        }
    } catch (error) {
        console.error('登录错误:', error);
        showError('网络错误，请稍后重试');
    } finally {
        setLoading(false);
    }
}

/**
 * 处理注册表单提交
 */
async function handleRegister(event) {
    event.preventDefault();
    
    if (isSubmitting) return;
    
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData);
    
    // 验证表单
    if (!validateRegisterForm(data)) {
        return;
    }
    
    setLoading(true);
    
    try {
        const response = await fetch('/api/auth/register-with-verification', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('注册成功！欢迎邮件已发送到您的邮箱');
            
            // 延迟跳转到登录页
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);
        } else {
            showError(result.error || '注册失败');
            if (result.details) {
                showError(result.details.join(', '));
            }
        }
    } catch (error) {
        console.error('注册错误:', error);
        showError('网络错误，请稍后重试');
    } finally {
        setLoading(false);
    }
}

/**
 * 验证登录表单
 */
function validateLoginForm(data) {
    let isValid = true;
    
    // 清除之前的错误
    clearErrors();
    
    if (!data.username_or_email) {
        showFieldError('username', '请输入用户名或邮箱');
        isValid = false;
    }
    
    if (!data.password) {
        showFieldError('password', '请输入密码');
        isValid = false;
    }
    
    return isValid;
}

/**
 * 验证注册表单
 */
function validateRegisterForm(data) {
    let isValid = true;
    
    // 清除之前的错误
    clearErrors();
    
    // 验证用户名
    if (!data.username) {
        showFieldError('username', '请输入用户名');
        isValid = false;
    } else if (data.username.length < 3 || data.username.length > 20) {
        showFieldError('username', '用户名长度应为3-20个字符');
        isValid = false;
    }
    
    // 验证邮箱
    if (!data.email) {
        showFieldError('email', '请输入邮箱');
        isValid = false;
    } else if (!isValidEmail(data.email)) {
        showFieldError('email', '邮箱格式不正确');
        isValid = false;
    }
    
    // 验证验证码
    if (!data.verification_code) {
        showFieldError('verification_code', '请输入邮箱验证码');
        isValid = false;
    } else if (data.verification_code.length !== 6) {
        showFieldError('verification_code', '验证码应为6位数字');
        isValid = false;
    }
    
    // 验证密码
    if (!data.password) {
        showFieldError('password', '请输入密码');
        isValid = false;
    } else if (!validatePasswordStrength(data.password)) {
        showFieldError('password', '密码不符合要求');
        isValid = false;
    }
    
    // 验证确认密码
    if (!data.confirm_password) {
        showFieldError('confirm_password', '请确认密码');
        isValid = false;
    } else if (data.password !== data.confirm_password) {
        showFieldError('confirm_password', '两次输入的密码不一致');
        isValid = false;
    }
    
    // 验证服务条款
    if (!data.agree_terms) {
        showFieldError('agree_terms', '请同意服务条款和隐私政策');
        isValid = false;
    }
    
    return isValid;
}

/**
 * 验证用户名
 */
function validateUsername() {
    const input = document.getElementById('username');
    const value = input.value.trim();
    
    if (!value) {
        showFieldError('username', '请输入用户名');
        return false;
    }
    
    if (value.length < 3 || value.length > 20) {
        showFieldError('username', '用户名长度应为3-20个字符');
        return false;
    }
    
    if (!/^[a-zA-Z0-9_]+$/.test(value)) {
        showFieldError('username', '用户名只能包含字母、数字和下划线');
        return false;
    }
    
    clearFieldError('username');
    return true;
}

/**
 * 验证邮箱
 */
function validateEmail() {
    const input = document.getElementById('email');
    const value = input.value.trim();
    
    if (!value) {
        showFieldError('email', '请输入邮箱');
        return false;
    }
    
    if (!isValidEmail(value)) {
        showFieldError('email', '邮箱格式不正确');
        return false;
    }
    
    clearFieldError('email');
    return true;
}

/**
 * 验证密码
 */
function validatePassword() {
    const input = document.getElementById('password');
    const value = input.value;
    
    if (!value) {
        showFieldError('password', '请输入密码');
        return false;
    }
    
    if (!validatePasswordStrength(value)) {
        showFieldError('password', '密码不符合要求');
        return false;
    }
    
    clearFieldError('password');
    return true;
}

/**
 * 验证确认密码
 */
function validateConfirmPassword() {
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');
    const password = passwordInput.value;
    const confirmPassword = confirmInput.value;
    
    if (!confirmPassword) {
        showFieldError('confirm_password', '请确认密码');
        return false;
    }
    
    if (password !== confirmPassword) {
        showFieldError('confirm_password', '两次输入的密码不一致');
        return false;
    }
    
    clearFieldError('confirm_password');
    return true;
}

/**
 * 验证密码强度
 */
function validatePasswordStrength(password) {
    const requirements = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        lowercase: /[a-z]/.test(password),
        number: /\d/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    };
    
    // 更新UI显示
    updatePasswordRequirements(requirements);
    
    return Object.values(requirements).every(req => req);
}

/**
 * 更新密码要求显示
 */
function updatePasswordRequirements(requirements) {
    const elements = {
        length: document.getElementById('req-length'),
        uppercase: document.getElementById('req-uppercase'),
        lowercase: document.getElementById('req-lowercase'),
        number: document.getElementById('req-number'),
        special: document.getElementById('req-special')
    };
    
    Object.keys(requirements).forEach(key => {
        const element = elements[key];
        if (element) {
            element.classList.toggle('valid', requirements[key]);
            element.classList.toggle('invalid', !requirements[key]);
        }
    });
}

/**
 * 检查用户名可用性
 */
async function checkUsernameAvailability() {
    const input = document.getElementById('username');
    const username = input.value.trim();
    
    if (!username || username.length < 3) return;
    
    try {
        const response = await fetch('/api/auth/check-username', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username })
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (!result.available) {
                showFieldError('username', '用户名已存在');
            } else {
                clearFieldError('username');
            }
        }
    } catch (error) {
        console.error('检查用户名错误:', error);
    }
}

/**
 * 检查邮箱可用性
 */
async function checkEmailAvailability() {
    const input = document.getElementById('email');
    const email = input.value.trim();
    
    if (!email || !isValidEmail(email)) return;
    
    try {
        const response = await fetch('/api/auth/check-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email })
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (!result.available) {
                showFieldError('email', '邮箱已被注册');
            } else {
                clearFieldError('email');
            }
        }
    } catch (error) {
        console.error('检查邮箱错误:', error);
    }
}

/**
 * 验证邮箱格式
 */
function isValidEmail(email) {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
}

/**
 * 显示字段错误
 */
function showFieldError(fieldName, message) {
    const errorElement = document.getElementById(`${fieldName}-error`);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
    
    const input = document.getElementById(fieldName);
    if (input) {
        input.classList.add('error');
    }
}

/**
 * 清除字段错误
 */
function clearFieldError(fieldName) {
    const errorElement = document.getElementById(`${fieldName}-error`);
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.classList.remove('show');
    }
    
    const input = document.getElementById(fieldName);
    if (input) {
        input.classList.remove('error');
    }
}

/**
 * 清除所有错误
 */
function clearErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.textContent = '';
        element.classList.remove('show');
    });
    
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.classList.remove('error');
    });
}

/**
 * 显示成功消息
 */
function showSuccess(message) {
    showMessage(message, 'success');
}

/**
 * 显示错误消息
 */
function showError(message) {
    showMessage(message, 'error');
}

/**
 * 显示消息
 */
function showMessage(message, type) {
    // 移除之前的消息
    const existingMessage = document.querySelector('.success-message, .error-message.global');
    if (existingMessage) {
        existingMessage.remove();
    }
    
    // 创建新消息
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'success' ? 'success-message' : 'error-message global';
    messageDiv.textContent = message;
    
    // 插入到表单前面
    const form = document.querySelector('.auth-form');
    if (form) {
        form.parentNode.insertBefore(messageDiv, form);
    }
    
    // 自动移除消息
    setTimeout(() => {
        if (messageDiv.parentNode) {
            messageDiv.parentNode.removeChild(messageDiv);
        }
    }, 5000);
}

/**
 * 设置加载状态
 */
function setLoading(loading) {
    isSubmitting = loading;
    
    const button = document.querySelector('.auth-button');
    if (button) {
        button.disabled = loading;
        button.classList.toggle('loading', loading);
    }
}

/**
 * 防抖函数
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}




// ==================== 验证码相关功能 ====================

/**
 * 处理邮箱变化
 */
function handleEmailChange() {
    const emailInput = document.getElementById('email');
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    const email = emailInput.value.trim();
    
    // 启用/禁用发送验证码按钮
    if (email && isValidEmail(email)) {
        sendCodeBtn.disabled = false;
    } else {
        sendCodeBtn.disabled = true;
    }
}

/**
 * 发送验证码
 */
async function handleSendVerificationCode() {
    const emailInput = document.getElementById('email');
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    const email = emailInput.value.trim();
    
    if (!email || !isValidEmail(email)) {
        showFieldError('email', '请输入有效的邮箱地址');
        return;
    }
    
    // 设置按钮加载状态
    setSendCodeLoading(true);
    
    try {
        const response = await fetch('/api/auth/send-verification-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                code_type: 'register'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('验证码已发送到您的邮箱，请查收');
            startCountdown();
            clearFieldError('email');
        } else {
            showFieldError('email', result.error || '发送验证码失败');
        }
    } catch (error) {
        console.error('发送验证码错误:', error);
        showFieldError('email', '网络错误，请稍后重试');
    } finally {
        setSendCodeLoading(false);
    }
}

/**
 * 重新发送验证码
 */
async function handleResendVerificationCode(event) {
    event.preventDefault();
    
    const emailInput = document.getElementById('email');
    const email = emailInput.value.trim();
    
    if (!email || !isValidEmail(email)) {
        showFieldError('email', '请输入有效的邮箱地址');
        return;
    }
    
    // 设置按钮加载状态
    setSendCodeLoading(true);
    
    try {
        const response = await fetch('/api/auth/resend-verification-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                code_type: 'register'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showSuccess('验证码已重新发送到您的邮箱');
            startCountdown();
            clearFieldError('email');
        } else {
            showFieldError('email', result.error || '重新发送验证码失败');
        }
    } catch (error) {
        console.error('重新发送验证码错误:', error);
        showFieldError('email', '网络错误，请稍后重试');
    } finally {
        setSendCodeLoading(false);
    }
}

/**
 * 验证验证码
 */
function validateVerificationCode() {
    const input = document.getElementById('verification_code');
    const value = input.value.trim();
    
    if (!value) {
        showFieldError('verification_code', '请输入验证码');
        return false;
    }
    
    if (value.length !== 6) {
        showFieldError('verification_code', '验证码应为6位数字');
        return false;
    }
    
    if (!/^\d{6}$/.test(value)) {
        showFieldError('verification_code', '验证码只能包含数字');
        return false;
    }
    
    clearFieldError('verification_code');
    return true;
}

/**
 * 设置发送验证码按钮加载状态
 */
function setSendCodeLoading(loading) {
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    if (sendCodeBtn) {
        sendCodeBtn.disabled = loading;
        sendCodeBtn.classList.toggle('loading', loading);
    }
}

/**
 * 开始倒计时
 */
function startCountdown() {
    const sendCodeBtn = document.getElementById('sendCodeBtn');
    const codeTimer = document.getElementById('codeTimer');
    const resendCodeLink = document.getElementById('resendCodeLink');
    const countdownElement = document.getElementById('countdown');
    
    let timeLeft = 60;
    
    // 显示倒计时
    codeTimer.style.display = 'inline';
    resendCodeLink.style.display = 'none';
    sendCodeBtn.disabled = true;
    
    const timer = setInterval(() => {
        timeLeft--;
        countdownElement.textContent = timeLeft;
        
        if (timeLeft <= 0) {
            clearInterval(timer);
            codeTimer.style.display = 'none';
            resendCodeLink.style.display = 'inline';
            sendCodeBtn.disabled = false;
        }
    }, 1000);
}

/**
 * 验证邮箱格式
 */
function isValidEmail(email) {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
}
