(function () {
    'use strict';

    describe('mode', function () {
        it("mode should find most common string in array", function () {
            var data = ['apple', 'pear', 'orange', 'apple', 'cherry', 'pear', 'pineapple', 'pear'];
            expect(mode(data)).toBe('pear');
        });
        it("mode should find most common number in array", function () {
            var data = [1, 1, 0, 0, 2, 1, 0, 0];
            expect(mode(data)).toBe(0);
        });
    });

})();
