# -*- coding: utf-8 -*-

from datetime import datetime
from odoo.exceptions import Warning
from odoo import fields, models, _


class Task(models.Model):
    _inherit = "project.task"

    task_datetime_start = fields.Datetime('Start Date')
    task_datetime_stop = fields.Datetime('Stop Date')
    time_tracking_ids = fields.One2many(
        comodel_name='task.time.track',
        inverse_name='task_id',
        string='Time Tracking')
    tracking_stage = fields.Selection(
        string='Tracking Stage',
        selection=[
                   ('none', 'None'),
                   ('start', 'Start'),
                   ('pause', 'Pause'),
                   ('stop', 'Stop')], default='none')
    quality_check = fields.Boolean('Quality Check')
    stage_duration = fields.Float('Stage Duration',
                                  compute='_compute_stage_duration')

    def _compute_stage_duration(self):
        for task in self:
            current_stage_id = task.stage_id and task.stage_id.id or False
            if current_stage_id and task.time_tracking_ids:
                time_ids = self.env['task.time.track'].search([
                    ('task_id', '=', task.id),
                    ('stage_id', '=', current_stage_id)])
                total_time = 0.0
                for time_id in time_ids:
                    total_time += time_id.duration
                task.stage_duration = total_time
            else:
                task.stage_duration = 0.0

    def time_start(self):
        self.ensure_one()
        self.tracking_stage = 'start'
        self.task_datetime_start = datetime.now()
        self.env['task.time.track'].create({
            'start_date': datetime.now(),
            'user_id': self.user_id and self.user_id.id or False,
            'project_id': self.project_id and self.project_id.id or False,
            'task_id': self.id,
            'stage_id': self.stage_id and self.stage_id.id or False,
            'duration': 0.0,
            'quality_check': self.quality_check,
        })

    def time_pause(self):
        self.ensure_one()
        self.tracking_stage = 'pause'
        tracking_ids = self.env['task.time.track'].search(
            [('task_id', '=', self.id), ('stop_date', '=', False),
             ('start_date', '!=', False)])

        if len(tracking_ids) == 1:
            tracking_ids[0].stop_date = datetime.now()
            tracking_ids[0]._calculate_duration()

    def time_stop(self):
        self.ensure_one()
        self.task_datetime_start = False
        self.task_datetime_stop = False
        self.tracking_stage = 'stop'
        tracking_ids = self.env['task.time.track'].search(
            [('task_id', '=', self.id), ('stop_date', '=', False),
             ('start_date', '!=', False)])
        if len(tracking_ids) == 1:
            tracking_ids[0].stop_date = datetime.now()
            tracking_ids[0]._calculate_duration()

    def write(self, values):
        for record in self:
            if record.tracking_stage != 'stop':
                if values.get('stage_id'):
                    raise Warning(
                        _("Please stop the task before change the stage!"))
                if values.get('user_id'):
                    raise Warning(
                        _(
                            "Please stop the task before assign it to other users!"))

        return super(Task, self).write(values)
