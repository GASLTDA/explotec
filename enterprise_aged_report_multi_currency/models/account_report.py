from odoo import models, api

class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    @api.multi
    def get_html(self, options, line_id=None, additional_context=None):
        templates = self.get_templates()
        report_manager = self.get_report_manager(options)
        report = {'name': self.get_report_name(),
                  'summary': report_manager.summary,
                  'company_name': self.env.user.company_id.name,}
        if line_id == None:
            lines = self.with_context(self.set_context(options)).get_lines(options, line_id=line_id)
        else:
            try:
                lines = self.with_context(self.set_context(options)).get_lines_no_currency(options, line_id=line_id)
            except:
                lines = self.with_context(self.set_context(options)).get_lines(options, line_id=line_id)
        if options.get('hierarchy'):
            lines = self.create_hierarchy(lines)

        footnotes_to_render = []
        if self.env.context.get('print_mode', False):
            # we are in print mode, so compute footnote number and include them in lines values, otherwise, let the js compute the number correctly as
            # we don't know all the visible lines.
            footnotes = dict([(str(f.line), f) for f in report_manager.footnotes_ids])
            number = 0
            for line in lines:
                f = footnotes.get(str(line.get('id')))
                if f:
                    number += 1
                    line['footnote'] = str(number)
                    footnotes_to_render.append({'id': f.id, 'number': number, 'text': f.text})

        rcontext = {'report': report,
                    'lines': {'columns_header': self.get_columns_name(options), 'lines': lines},
                    'options': options,
                    'context': self.env.context,
                    'model': self,
                    }
        if additional_context and type(additional_context) == dict:
            rcontext.update(additional_context)
        render_template = templates.get('main_template', 'account_reports.main_template')
        if line_id is not None:
            render_template = templates.get('line_template', 'account_reports.line_template')
        html = self.env['ir.ui.view'].render_template(
            render_template,
            values=dict(rcontext),
        )
        if self.env.context.get('print_mode', False):
            for k,v in self.replace_class().items():
                html = html.replace(k, v)
            # append footnote as well
            html = html.replace(b'<div class="js_account_report_footnotes"></div>', self.get_html_footnotes(footnotes_to_render))
        return html