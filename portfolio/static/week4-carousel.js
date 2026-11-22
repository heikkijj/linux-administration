document.querySelectorAll('[data-carousel]').forEach((carousel) => {
    const slides = Array.from(carousel.querySelectorAll('.carousel-slide'));
    const previousButton = carousel.querySelector('[data-carousel-previous]');
    const nextButton = carousel.querySelector('[data-carousel-next]');
    const controls = carousel.querySelector('[data-carousel-controls]');
    const indicators = carousel.querySelector('[data-carousel-indicators]');
    const status = carousel.querySelector('[data-carousel-status]');

    if (!slides.length || !previousButton || !nextButton || !controls || !indicators || !status) {
        return;
    }

    let activeIndex = 0;

    const indicatorButtons = slides.map((slide, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = String(index + 1);
        button.setAttribute('aria-label', `Show step ${index + 1}`);
        button.addEventListener('click', () => showSlide(index));
        indicators.append(button);
        return button;
    });

    function showSlide(index) {
        activeIndex = index;
        slides.forEach((slide, slideIndex) => {
            slide.hidden = slideIndex !== activeIndex;
        });
        indicatorButtons.forEach((button, buttonIndex) => {
            if (buttonIndex === activeIndex) {
                button.setAttribute('aria-current', 'step');
            } else {
                button.removeAttribute('aria-current');
            }
        });
        previousButton.disabled = activeIndex === 0;
        nextButton.disabled = activeIndex === slides.length - 1;
        status.textContent = `Step ${activeIndex + 1} of ${slides.length}`;
    }

    previousButton.addEventListener('click', () => showSlide(activeIndex - 1));
    nextButton.addEventListener('click', () => showSlide(activeIndex + 1));

    showSlide(activeIndex);
    controls.hidden = false;
});
