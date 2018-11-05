Vue.component('type-app',{
    template: '#types-app-template',
    data: function(){
        return {
            type: typeData,
            typeMenuVisible: false
        }
    },
    methods: {
        toggleMenu: function () {
            this.typeMenuVisible = !this.typeMenuVisible;
        }
    },
    computed: {
        isMobile: function () {
            if (window.innerWidth < 600) return true;
            return false; 
        }
    }
});