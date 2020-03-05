-- pylint: disable=file-not-used
-- the file is used by mis_unpaid_invoice.py
CREATE OR REPLACE VIEW mis_unpaid_invoice AS (
SELECT    aml.id as id,
    'unpaid invoice' AS line_type,
    ai.company_id,
    aml.journal_id,
    aml.name,
    aml.move_id,
    ai.id AS invoice_id,
    aml.product_id,
    aml.analytic_account_id,
    aml.date,
    aml.account_id,
    aml.debit,
    aml.credit
FROM (account_move_line aml
     LEFT outer JOIN account_invoice ai ON ai.move_id = aml.move_id)
WHERE ai.state::text = 'open'::text 
    AND (ai.type::text = ANY (ARRAY['out_invoice'::character varying::text, 'out_refund'::character varying::text]))
)
