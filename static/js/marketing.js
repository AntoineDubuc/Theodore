// Sales Scout Marketing JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all marketing features
    initScrollEffects();
    initTypingAnimation();
    initCounterAnimation();
    initSmoothScrolling();
    initMobileMenu();
    initHeroDemo();
    
    // Start typing animations after a delay
    setTimeout(() => {
        startTypingAnimations();
    }, 1000);
});

// Header scroll effects
function initScrollEffects() {
    const header = document.querySelector('.marketing-header');
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

// Typing animation for demo section
function initTypingAnimation() {
    const typingElements = document.querySelectorAll('.typing-animation');
    
    typingElements.forEach(element => {
        const text = element.getAttribute('data-text');
        element.textContent = '';
        element.setAttribute('data-original-text', text);
    });
}

function startTypingAnimations() {
    const typingElements = document.querySelectorAll('.typing-animation');
    
    typingElements.forEach((element, index) => {
        setTimeout(() => {
            typeText(element);
        }, index * 800);
    });
}

function typeText(element) {
    const text = element.getAttribute('data-original-text');
    let index = 0;
    
    const typeInterval = setInterval(() => {
        element.textContent = text.slice(0, index + 1);
        index++;
        
        if (index >= text.length) {
            clearInterval(typeInterval);
            element.classList.remove('typing-animation');
        }
    }, 50);
}

// Counter animation for statistics
function initCounterAnimation() {
    const counters = document.querySelectorAll('.counter');
    const observerOptions = {
        threshold: 0.5,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounter(entry.target);
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    counters.forEach(counter => observer.observe(counter));
}

function animateCounter(counter) {
    const target = parseInt(counter.getAttribute('data-target'));
    const duration = 2000;
    const increment = target / (duration / 16);
    let current = 0;
    
    const updateCounter = () => {
        current += increment;
        if (current < target) {
            counter.textContent = Math.floor(current);
            requestAnimationFrame(updateCounter);
        } else {
            counter.textContent = target;
        }
    };
    
    updateCounter();
}

// Smooth scrolling for anchor links
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Mobile menu functionality
function initMobileMenu() {
    const toggle = document.querySelector('.mobile-menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (toggle && navLinks) {
        toggle.addEventListener('click', () => {
            toggle.classList.toggle('active');
            navLinks.classList.toggle('active');
        });
    }
}

// Hero demo interactions
function initHeroDemo() {
    const demoInput = document.querySelector('.demo-input input');
    const demoBtn = document.querySelector('.demo-btn');
    const outputItems = document.querySelectorAll('.output-item');
    
    if (demoBtn) {
        demoBtn.addEventListener('click', () => {
            // Simulate processing
            demoBtn.textContent = 'Processing...';
            demoBtn.disabled = true;
            
            // Reset and restart typing animations
            setTimeout(() => {
                outputItems.forEach(item => {
                    const valueEl = item.querySelector('.output-value');
                    if (valueEl && valueEl.hasAttribute('data-text')) {
                        valueEl.textContent = '';
                        valueEl.classList.add('typing-animation');
                    }
                });
                
                startTypingAnimations();
                
                setTimeout(() => {
                    demoBtn.textContent = 'Analyze';
                    demoBtn.disabled = false;
                }, 3000);
            }, 500);
        });
    }
}

// Scroll to signup section
function scrollToSignup() {
    const signupSection = document.getElementById('signup');
    if (signupSection) {
        signupSection.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Show demo modal (placeholder)
function showDemo() {
    // This would open a demo modal or redirect to a demo page
    alert('Demo coming soon! Start your free trial to see Sales Scout in action.');
}

// Intersection Observer for fade-in animations
function initFadeInAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Add fade-in classes to elements
    const fadeElements = document.querySelectorAll('.feature-card, .partner-card, .problem-item, .solution-item');
    fadeElements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(el);
    });
}

// Initialize fade animations after DOM is ready
setTimeout(initFadeInAnimations, 500);

// Form validation and enhancement
function initFormEnhancements() {
    const signupForm = document.querySelector('.signup-form');
    
    if (signupForm) {
        signupForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            
            // Show loading state
            submitBtn.innerHTML = '<span>⏳</span> Creating Account...';
            submitBtn.disabled = true;
            
            // Simulate API call
            setTimeout(() => {
                // In a real app, this would submit to the server
                alert('Thanks for signing up! Check your email for next steps.');
                
                // Reset form
                this.reset();
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 2000);
        });
        
        // Enhanced input interactions
        const inputs = signupForm.querySelectorAll('input');
        inputs.forEach(input => {
            input.addEventListener('focus', function() {
                this.parentElement.classList.add('focused');
            });
            
            input.addEventListener('blur', function() {
                this.parentElement.classList.remove('focused');
                if (this.value) {
                    this.parentElement.classList.add('filled');
                } else {
                    this.parentElement.classList.remove('filled');
                }
            });
        });
    }
}

// Initialize form enhancements
initFormEnhancements();

// Parallax effect for hero section
function initParallaxEffect() {
    const heroSection = document.querySelector('.hero-section');
    
    if (heroSection) {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallax = scrolled * 0.3;
            
            heroSection.style.transform = `translateY(${parallax}px)`;
        });
    }
}

// Initialize parallax (disabled by default for performance)
// initParallaxEffect();

// Easter egg: Konami code
let konamiCode = [];
const targetCode = [38, 38, 40, 40, 37, 39, 37, 39, 66, 65]; // Up Up Down Down Left Right Left Right B A

document.addEventListener('keydown', function(e) {
    konamiCode.push(e.keyCode);
    
    if (konamiCode.length > targetCode.length) {
        konamiCode.shift();
    }
    
    if (konamiCode.length === targetCode.length && 
        konamiCode.every((code, index) => code === targetCode[index])) {
        
        // Easter egg activated
        document.body.style.animation = 'rainbow 2s infinite';
        
        setTimeout(() => {
            document.body.style.animation = '';
            alert('🎉 Easter egg found! You get +1 free month when you sign up!');
        }, 2000);
        
        konamiCode = [];
    }
});

// Add rainbow animation for easter egg
const style = document.createElement('style');
style.textContent = `
    @keyframes rainbow {
        0% { filter: hue-rotate(0deg); }
        100% { filter: hue-rotate(360deg); }
    }
`;
document.head.appendChild(style);

// Track user interactions for analytics (placeholder)
function trackEvent(eventName, properties = {}) {
    // In a real app, this would send data to analytics service
    console.log('Analytics Event:', eventName, properties);
}

// Track key interactions
document.addEventListener('click', function(e) {
    if (e.target.matches('.btn-primary')) {
        trackEvent('CTA_Clicked', {
            button_text: e.target.textContent.trim(),
            page_section: getPageSection(e.target)
        });
    }
});

function getPageSection(element) {
    const section = element.closest('section');
    return section ? section.className.split(' ')[0] : 'unknown';
}

// Global functions for HTML onclick handlers
window.scrollToSignup = scrollToSignup;
window.showDemo = showDemo;