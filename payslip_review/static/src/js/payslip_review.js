odoo.define("payslip_review.payslip_review", function(require) {
    "use strict";
     
    var core = require("web.core");
    var dataset = require("web.data");
    var Widget = require("web.Widget");
    var _t = core._t;
    var QWeb = core.qweb;

    var payslip_review = Widget.extend({
        template: "Mainpage",
        events:{
            'click #search-payslip' : 'search_payslsip',
            'click #print-payslip' : 'print_payslip',
            'click .payslip-compute' : 'payslip_compute',
            'click .payslip-confirm' : 'payslip_confirm',
        },
        start: function () {
            return $.when(
                new SearchForm(this).appendTo(this.$('.payslip_review_search_area')),
                new ResultForm(this).appendTo(this.$('.payslip_review_result_area'))
            );
        },
        print_payslip:function(){
            window.print();  
        },
        search_payslsip:function(){
            var self = this;
            self.$('.payslip_data tbody').html('')
            var month = self.$('.payslip-search-from #month').val()
            var year = self.$('.payslip-search-from #year').val()
            var emp_id = self.$('.payslip-search-from #employee_name').val()
            var batch = self.$('.payslip-search-from #batch').val()
            var payslip = this._rpc({
                model:'hr.payslip',
                method: 'payslip_salary_data',
                args: [month,year,emp_id,batch],
            }).then(function(results){
                _(results).each(function (item) {
                    self.$('.payslip_data tbody').append(QWeb.render('ResultFormCell', {item: item}));
                });
            }).then(function(res){
                    var column_num = document.getElementById('payslip_data').rows[0].cells.length;
                    for (var i = 0;i < column_num;i++) {
                        if (i >= 6) {
                            var totalRule = self.computeTableColumnTotal("payslip_data",i);
                            try {
                                var totalRuleElem = window.document.getElementById("footer_" + i.toString());
                                totalRuleElem.innerHTML = totalRule;
                            }
                            catch (ex){
                                console.log("Exception in function finishTable()\n" + ex);
                            }   
                        }
                    }
                });
        },
        payslip_compute:function(e){
            var self = this;
            var line_id = parseInt($(e.currentTarget).attr('lid'));
            var row = $(e.currentTarget).parent().parent().parent();
            var row_inputs = row.find($('.salary-input'));
            
            if (row_inputs.length == 0) {
                var payslip = this._rpc({
                    model:'hr.payslip',
                    method: 'compute_sheet',
                    args: [line_id],
                }).then(function(results){
                    self.search_payslsip(this);
                });
            }
            else{
                row_inputs.each(function(item){
                    var _input = $(row_inputs[item]);
                    var input_id = _input.attr('lid');
                    var amount = _input.val();
                    var payslip = self._rpc({
                        model:'hr.payslip',
                        method: 'payslip_update_input',
                        args: [input_id,amount],
                    }).then(function(results){
                        if (item == row_inputs.length -1) {
                            var payslip = self._rpc({
                                model:'hr.payslip',
                                method: 'compute_sheet',
                                args: [line_id],
                            }).then(function(results){
                                self.search_payslsip(this);
                            });
                        }
                    });
                });
            }
        },
        payslip_confirm:function(e){
            var self = this;
            var line_id = parseInt($(e.currentTarget).attr('lid'));
            var row = $(e.currentTarget).parent().parent().parent();
            var row_inputs = row.find($('.salary-input'));
            
            if (row_inputs.length == 0) {
                var compute_payslip = self._rpc({
                    model:'hr.payslip',
                    method: 'action_payslip_done',
                    args: [line_id],
                }).then(function(results){
                    self.search_payslsip(this);
                });
            }
            else{
                row_inputs.each(function(item){
                    var _input = $(row_inputs[item]);
                    var input_id = _input.attr('lid');
                    var amount = _input.val();
                    var compute_payslip = self._rpc({
                        model:'hr.payslip',
                        method: 'payslip_update_input',
                        args: [input_id,amount],
                    }).then(function(results){
                        if (item == row_inputs.length -1) {
                            self._rpc({
                                model:'hr.payslip',
                                method: 'action_payslip_done',
                                args: [line_id],
                            }).then(function(results){
                                self.search_payslsip(this);
                            });
                        }
                    });
                });
            }
        },
        computeTableColumnTotal:function(tableId, colNumber)
        {
            var result = 0;
            try
            {
              var tableElem = window.document.getElementById(tableId); 		   
              var tableBody = tableElem.getElementsByTagName("tbody").item(0);
              var i;
              var howManyRows = tableBody.rows.length;
              for (i=1; i<(howManyRows-1); i++) // skip first and last row (hence i=1, and howManyRows-1)
              {
                 var thisTrElem = tableBody.rows[i];
                 var thisTdElem = thisTrElem.cells[colNumber];			
                 var thisTextNode = thisTdElem.childNodes.item(0);
                 // try to convert text to numeric
                 var thisNumber = parseFloat(thisTextNode.data);
                 // if you didn't get back the value NaN (i.e. not a number), add into result
                 if (!isNaN(thisNumber))
                   result += thisNumber;
               } // end for
                   
            } // end try
            catch (ex)
            {
               console.log("Exception in function computeTableColumnTotal()\n" + ex);
               result = 0;
            }
            finally
            {
               return result;
            }
              
        }
    });
    core.action_registry.add("payroll.review", payslip_review);
    
    
    var SearchForm = Widget.extend({
        template: 'SearchForm',
        start: function () {
            var self = this;
            this._rpc({
                model:'hr.employee',
                method: 'search_read',
                args: [[]],
            }).then(function (results) {
                    var employee_name = "<option value='0'></option>"
                    _(results).each(function (item) {
                        employee_name += '<option value='+item.id+'>'+item.name+'</option>';
                    });
                    self.$("#employee_name").html(employee_name);
                });
            
            this._rpc({
                model:'hr.payslip.run',
                method: 'search_read',
                args: [[]],
            }).then(function (results) {
                    var batch_name = "<option value='0'></option>"
                    _(results).each(function (item) {
                        batch_name += '<option value='+item.id+'>'+item.name+'</option>';
                    });
                    self.$("#batch").html(batch_name);
                });
            
            var compute_payslip = this._rpc({
                    model:'hr.payslip',
                    method: 'employee_payslip_years',
                    args: [],
            }).then(function(results){
                    var employee_name = "<option value='0'></option>"
                    _(results).each(function (item) {
                        employee_name += '<option value='+item.year+'>'+item.year+'</option>';
                    });
                    self.$("#year").html(employee_name);
                });
        }
    });
    
    var ResultForm = Widget.extend({
        template: 'ResultForm'
    });
});