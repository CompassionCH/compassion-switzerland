-- pylint: disable=file-not-used
-- the file is used by mis_spn_event_info.py
CREATE OR REPLACE VIEW mis_spn_event_info AS (
select row_number() OVER (ORDER BY a.line_type,A.table_ID) as id,a.*
from (
select cec.id as table_id,
    cec.type as line_type,
     1 as company_id,
        cec.name,
        cec.analytic_id as analytic_account_id,
        cec.start_date as date,ru.partner_id as user_id ,cec.partner_id,
        null as invoice_id,
        2832 as account_id,
        case
        when cec.type='sport' and ath.lete >0 then ath.lete
        else 1 end as debit,
        0 as credit,
        cec.id as event_id,
        cec.event_type_id
        from crm_event_compassion cec
        left join res_users ru on cec.user_id=ru.id
        left join (
        select cec.id,
        case
        when count(distinct reg.reg)=0 then count(distinct p.partner_id)
        else count(distinct reg.reg) end as lete
        from crm_event_compassion cec
        left outer join partners_to_staff_event p on p.event_id=cec.id
        full outer join
        (
        select ee.compassion_event_id as event_id, (er.id) as reg
        from event_registration er
        left outer join event_event ee on ee.id=er.event_id
        ) reg on reg.event_id=cec.id
        group by cec.id
        having (count(distinct reg.reg)>0 or count(distinct p.partner_id)>0)) ath on ath.id=cec.id

union all
    select rc.id as table_id,
    case
    when rc.parent_id is null then 'acquisition'
    else 'sub'
    end as line_type,
     1 as company_id,
        rc.name,
        rco.analytic_id as analytic_account_id,
        rc.activation_date as date,rc.user_id,rc.correspondent_id as partner_id,0 as invoice_id,
        2858 as account_id,
        1 as debit,
        0 as credit,
        rco.event_id,
        cec.event_type_id
        from recurring_contract rc
        left outer join recurring_contract_origin rco on rc.origin_id=rco.id
        left join crm_event_compassion cec on rco.event_id=cec.id
        where rc.activation_date is not null
        and rc.type in ('SC','S')
union all
    select rc.id as table_id,
     'depart/cancel' as line_type,
     1 as company_id,
     rc.name,
     rco.analytic_id as analytic_account_id,
        rc.end_date as date,
        rc.user_id,
        rc.correspondent_id as partner_id,
        0 as invoice_id,
        2858 as account_id,
        0 as debit,
        1 as credit,
        rco.event_id,
        cec.event_type_id
        from recurring_contract rc
        left outer join recurring_contract_origin rco on rc.origin_id=rco.id
        left join crm_event_compassion cec on rco.event_id=cec.id
        where rc.end_date is not null
        and rc.type in ('SC','S')
union all

    select aml.id as table_id,
     'move line' as line_type,
     aml.company_id,
     aml.name,
     analytic_account_id,
     aml.date,
     ru.partner_id as user_id,
     aml.partner_id,
     aml.invoice_id,
     aml.account_id,
     debit,
     credit,
     aaa.event_id,
     cec.event_type_id
      from account_move_line aml
        left outer join account_analytic_account aaa on aaa.id=aml.analytic_account_id
        left outer join account_account aa on aa.id=aml.account_id
        left outer join account_invoice ai on ai.id=aml.invoice_id
        left join crm_event_compassion cec on aaa.event_id=cec.id
        left join res_users ru on ai.user_id=ru.id
        where aa.code='4850' or aa.user_type_id=8 and ai.invoice_type not in ('sponsorship', 'gift')
) a
    )
