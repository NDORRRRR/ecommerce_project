document.addEventListener('DOMContentLoaded', function() {
	let backToTopBtn = document.getElementById('btn-back-to-top');

    if (backToTopBtn) {
    	window.onscroll = function () {
            scrollFunction();
        };

        function scrollFunction() {
            if (
                document.body.scrollTop > 200 ||
                document.documentElement.scrollTop > 200
            ) {
                backToTopBtn.style.display = 'block';
            } else {
                backToTopBtn.style.display = 'none';
            }
        }

        backToTopBtn.addEventListener('click', function() {
            document.body.scrollTop = 0; // Untuk Safari
            document.documentElement.scrollTop = 0; // Untuk Chrome, Firefox, IE dan Opera
        });
    }
});