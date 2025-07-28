# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Starting post-migration for next_of_kin relationship field.")

    # 1. Get all unique old selection values
    cr.execute(
        "SELECT DISTINCT relationship_selection_tmp FROM naseni_hr_next_of_kin WHERE relationship_selection_tmp IS NOT NULL;"
    )
    old_values = [row[0] for row in cr.fetchall()]

    # 2. Create new Many2one records for each unique value (if not already present)
    for value in old_values:
        cr.execute("SELECT id FROM nok_relationship WHERE name = %s", (value,))
        result = cr.fetchone()
        if result:
            rel_id = result[0]
        else:
            cr.execute(
                "INSERT INTO nok_relationship (name) VALUES (%s) RETURNING id;",
                (value,),
            )
            rel_id = cr.fetchone()[0]
        # 3. Update next_of_kin records to point to the new Many2one record
        cr.execute(
            """
            UPDATE naseni_hr_next_of_kin
            SET relationship = %s
            WHERE relationship_selection_tmp = %s
        """,
            (rel_id, value),
        )

    # 4. Drop the temporary column
    cr.execute(
        "ALTER TABLE naseni_hr_next_of_kin DROP COLUMN relationship_selection_tmp;"
    )

    # 5. Drop the old selection field
    cr.execute("ALTER TABLE naseni_hr_next_of_kin DROP COLUMN relationship;")
    # 6. Remove the ir.model.fields reference
    cr.execute(
        """
        DELETE FROM ir_model_fields
        WHERE model = 'naseni_hr.next_of_kin' AND name = 'relationship';
    """
    )
    _logger.info(
        "Post-migration completed: relationship field migrated to Many2one, old selection field and temp column dropped, ir.model.fields reference removed."
    )
