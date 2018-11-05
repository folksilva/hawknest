Vue.use(VueMaterial.default)

var app = new Vue({
    el: '#app',
    data: {
        width: window.innerWidth,
        menuVisible: false,
        mainSearchFocus: false,
        type: typeData || {},
        group: groupData || {},
        messages: messagesData || [],
        permissions: permissionsData || {},
        document: documentData || {}
    },
    methods: {
        toggleMainMenu: function () {
            this.menuVisible = !this.menuVisible;
        },
        showNotification: function (message) {
            return this.messages ?  this.messages.indexOf(message) > -1 : false;
        },
        hideNotification: function (message) {
            if (this.messages) {
                let index = this.messages.indexOf(message);
                this.messages.splice(index, 1);
            }
        },
        openPath: function(path){
            window.location = path;
        }
    },
    computed: {
        isMobile: function () {
            if (this.width < 600) return true;
            return false; 
        }
    },
    mounted: function(){
        document.body.className = "on";
    }
});

window.addEventListener('resize', function () {
    app._data.width = window.innerWidth;
})