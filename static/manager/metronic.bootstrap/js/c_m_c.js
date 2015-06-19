var handleDateRangePickers = function () {
    if (!jQuery().daterangepicker) {
        return;
    }

    $('#form-date-range').daterangepicker({
        ranges: {
            '今天': ['today', 'today'],
            '昨天': ['yesterday', 'yesterday'],
            '过去七天': [Date.today().add({
                    days: -6
                }), 'today'],
            '过去30天': [Date.today().add({
                    days: -30
                }), 'today'],
            '本月': [Date.today().moveToFirstDayOfMonth(), Date.today().moveToLastDayOfMonth()],
            '上月': [Date.today().moveToFirstDayOfMonth().add({
                    months: -1
                }), Date.today().moveToFirstDayOfMonth().add({
                    days: -1
                })]
        },
        opens: 'left',
        //format: 'MM/dd/yyyy',
        format: 'yyyy-MM-dd',
        separator: ' to ',
        startDate: Date.today().add({
            days: -30
        }),
        endDate: Date.today(),
        minDate: '2012-01-01',
        maxDate: '2024-12-31',
        locale: {
            applyLabel: '确定',
            fromLabel: '起始',
            toLabel: '截止',
            customRangeLabel: '自定义范围',
            daysOfWeek: ['日', '一', '二', '三', '四', '五', '六'],
            monthNames: ['一月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '十一', '十二'],
            firstDay: 1
        },
        showWeekNumbers: false,
        buttonClasses: ['btn-danger']
    },

    function (start, end) {
        $('#form-date-range span').html(start.toString('yyyy-MM-dd') + ' 至 ' + end.toString('yyyy-MM-dd'));
        $('#hidStart').val(start.toString('yyyy-MM-dd'));
        $('#hidEnd').val(end.toString('yyyy-MM-dd'));
    });

    $('#form-date-range span').html(Date.today().add({
        days: -30
    }).toString('yyyy-MM-dd') + ' 至 ' + Date.today().toString('yyyy-MM-dd'));
    
    $("#hidStart").val(Date.today().add({days: -30}).toString('yyyy-MM-dd'));
    $("#hidEnd").val(Date.today().toString('yyyy-MM-dd'));

}

handleDateRangePickers();